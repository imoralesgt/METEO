'''
Third-party dependencies
-----------------------------------------------
	+ paho-mqtt (https://github.com/eclipse/paho.mqtt.python)
'''



import paho.mqtt.client as mqtt


import threading
import socket
import os
import time

import piSensors.BME680_METEO
import piSensors.BH1750_METEO
from defs import * #IRM Global definitions, such as a C Header Definitions File


'''
TODO:
	- Connect to MQTT Broker in object constructor
		+ Subscribe to every single settings topic
		+ Show performance and broker info by subscribing to special $SYS topics 
  		  (https://www.hivemq.com/blog/mqtt-essentials-part-5-mqtt-topics-best-practices)
	- Set sampling rates by reading this value from a specific MQTT Topic (which we must be suscribed to)
	- Sample each sensor using separate threads
		+ Create a generic sampling method, which receives the sensor name as parameter
			~ sampleSensor (sensorName, samplingRate)
		+ Generate as many threads running this method as required
		+ Kill sampling threads during object destruction
		+ Implement a mutual-exclusion mechanism to avoid access violations
	- Send data sensors' data via MQTT using topics to distribute data into different channels
	- Each "METEO" station MUST have a vaild (integer type) identifier, starting from 0
	- Topics should follow the following template:
		+ METEO/<stationNumber>/<sensor>
		+ Valid <stationNumber> (identifiers) are integers from 0 to N-1
		+ Valid <sensor> are:
			~ Temperature (Environmental temperature) [temp]
			~ Humidity (Relative humidity) [hum]
			~ Pressure (Local atmospheric pressure) [pres]
			~ Light (Incident light measurement) [light]
			~ AirQuality (Air quality as pollution measurement) [airQ]
			~ PPM (Raw particle count) [ppm]
	- A special topic may be used to set/get the sampling period dymanically
		+ METEO/Settings/SamplingRate/<sensor>
		+ <sensor> field (sub-topic) is the same as described before
		+ Sampling rate value must be validated to remain between a valid range
			~ Min sampling rate 1 minute
			~ Max sampling rate 120 minutes
			~ If a sampling rate (SR) out of these limits is set, a default value will be chosen \
			  if a prior valid SR wasn't set yet; otherwise, the last valid SR will remain active

'''

class Meteo(object):


	'''
	=======================================================
	IMR Class-related globals
	=======================================================	
	'''
	SENSOR_NAMES = AVAILABLE_SENSORS



	'''
	=======================================================
	IRM Object constructor
	=======================================================
	'''
	def __init__(self, DEBUG = 0):
		self.__initSensorSR()
		self.DEBUG = DEBUG
		self.ERRORS = ERRORS

		self.__initMQTTClient()
		

	'''
	=======================================================
	IRM Private methods encapsulation
	=======================================================
	'''

	'''
	IRM Setters and Getters
	'''

	def __getDefaultSR(self):
		return DEFAULT_SAMPLING_RATE

	def __getMinMaxSR(self):
		return (MIN_SAMPLING_RATE, MAX_SAMPLING_RATE)


	'''
	IRM Other private methods
	'''

	# IRM Setup default sensor sampling rates
	def __initSensorSR(self):
		self.__SR = {}
		sensorNames = self.getSensorNames()
		for i in sensorNames:
			self.__SR[i] = self.__getDefaultSR()


	# IRM Connects to MQTT Broker as client
	def __setupMQTTClient(self, address, port):
		self.mqttC = mqtt.Client()
		try:
			self.mqttC.connect(address, port)
		except socket.error:
			if self.DEBUG:
				print 'Could not connect to Mosquitto broker at ' + str(address) + ':' + str(port)
				print 'Restarting service and trying to reconnect...'

			os.system("sudo service mosquitto restart")
			time.sleep(1)
			self.mqttC.reconnect()


	# IRM Subscribes to a determined topic using a determined QoS
	def __mqttSubscribe(self, topic, qos = 0):
		self.mqttC.subscribe(topic, qos)

	# IRM Initializes MQTT Client according to this project's requirements
	def __initMQTTClient(self):
		broker = MQTT_BROKER
		port   = MQTT_PORT
		self.__setupMQTTClient(broker, port)

		# IRM Subscribe to every "settings" sub-topic available
		settingsTopic = ROOT_TOPIC + '/' + SETTINGS_TOPIC + '/' + MQTT_MULTI_LEVEL
		self.__mqttSubscribe(settingsTopic)


	'''
	=======================================================
	IRM Public Methods
	=======================================================
	'''

	'''
	IRM Setters and Getters
	'''

	# IRM set sampling rate in seconds.
	def setSR(self, sensor, interval):
		(minSR, maxSR) = self.__getMinMaxSR()

		sensorNames = self.getSensorNames()

		if sensor in sensorNames: # IRM Valid/Invalid sensor name
			if interval >= minSR and interval <= maxSR: # IRM Valid/Invalid interval
				self.__SR[sensor] = interval
			else:
				return self.ERRORS[INVALID_SAMPLING_RATE] # IRM Invalid sampling rate
				
				if self.DEBUG:
					print 'Invalid sampling rate (SR): ' + str(interval) + ' seconds'
					print 'SR must be between [' + str(minSR) + ',' + str(maxSR) + ']'
					
		else:
			return self.ERRORS[INVALID_SENSOR_NAME] # IRM
			
			if self.DEBUG:
				print 'Sensor "' + sensor + '" not valid.'
				print 'Sensor name must be one of the following in the list' + str(sensorNames)
				

		return 0 # IRM No errors during operation

	def getSensorNames(self):
		return self.SENSOR_NAMES

	def getSRvalues(self): #IRM Sampling rate values for each sensor
		return self.__SR

	'''
	IRM Other public methods
	'''

	








def testBench():
	myMeteo = Meteo(1) # IRM Enable Debugging

	# IRM Playing out with sampling rate values
	print myMeteo.getSensorNames()
	print myMeteo.getSRvalues()

	print myMeteo.setSR('temp', 500)
	print myMeteo.setSR('Temp', 600) # IRM Wrong value, should return an error code
	print myMeteo.setSR('airQ', 5*60)

	print myMeteo.getSRvalues()






if __name__ == '__main__':
	testBench()

