#! /usr/bin/python

'''
Third-party dependencies
-----------------------------------------------
	+ paho-mqtt (https://github.com/eclipse/paho.mqtt.python)
	+ RPi.GPIO  (https://pypi.org/project/RPi.GPIO/)
'''


import paho.mqtt.client as mqttClient


import threading
import socket
import os
import time

import piSensors.BME680_METEO as BME680
import piSensors.BH1750_METEO as BH1750
from defs import * #IRM Global definitions, such as a C Header Definitions File

from ui import UI_METEO as ui # IRM LED and Push-Button interface


'''
TODO list: check readme at github repo (https://github.com/imoralesgt/METEO)
'''


'''
========================================================
IRM Mutual-exclusion object to avoid simultaneous access
tries to a particular shared resource/sensor/device.

Its usage implies locking operation until the execution
queue is empty. Same object may be invoked/modified from
different threads.
========================================================
'''
class Mutex(object):

	def __init__(self, autoExec = True, DEBUG = False):
		# IRM determines whether the shared resource is locked or unlocked
		self.__locked = False 

		# IRM Queue as a list of pending executions from multiple sources
		# Each element within this list must accomplish with the following format:
		# [methodName, [list of parameters]]
		self.executionQueue = []

		# IRM Mutex is used only as a semaphore? or should it also execute pending methods?
		self.__autoExec = autoExec

		# IRM Debug enabled/disabled
		self.DEBUG = DEBUG


	'''
	=======================================================
	IRM Private methods encapsulation
	=======================================================
	'''		

	# IRM Reserved method. Updates and executes remaining (method, (parameters)) pairs if present
	def __updateLockState(self):
		if len(self.executionQueue) > 0: # IRM If there is still at least 1 pending ejecution
			self.__locked = True
			execPair = self.executionQueue.pop(0)
			if self.DEBUG:
				print execPair
			return self.__execute(execPair[0], execPair[1]) # IRM (Method, Parameters)
		else:
			self.unlock() # IRM If nothing pending, free (unlock) the resource
		
	# IRM Run a determined method with the passed parameters, which are then unpacked using (*)
	def __execute(self, method, parameters):
		data = method(*parameters) # IRM Run required method with passed parameters
		return data

	'''
	=======================================================
	IRM Public Methods
	=======================================================
	'''

	# IRM Reserve shared resource and queue a (method, [parameters]) pair
	# to be executed in a FIFO fashion. 
	def lock(self, method = None, parameters = ['Resource locked']): 
		self.__locked = True
		if self.__autoExec: # IRM Should I run something while locked?
			# IRM A tuple to represent (method, (parameters)) in queue
			self.executionQueue.append([method, parameters])

			# IRM Check whether resource is busy or not and return the
			# result of executing the queued method
			return self.__updateLockState()

	# IRM Only should be invoked by user if AutoExec is disabled!
	def unlock(self):
		if not self.__autoExec:
			self.__locked = False
			return True
		else:
			return None

	# IRM Only should be invoked by user if AutoExec is disabled!
	def isMutexLocked(self):
		if not self.__autoExec:
			return self.__locked
		else:
			return None

	def getAutoExec(self):
		return self.__autoExec


'''
=======================================================
IRM Main METEO front-end class for user-level access
=======================================================
'''
class Meteo(object):


	'''
	=======================================================
	IMR Class-related globals
	=======================================================	
	'''
	
	# IRM Variable names (Pressure, Temperature, Humidity, etc.)
	SENSOR_NAMES = AVAILABLE_SENSORS

	# IRM What variables should I measure with each sensor?
	# Temperature -> BME680
	# Pressure    -> BME680
	# Light       -> BH1750
	# Humidity    -> BME680 
	# etc ...
	SENSORS_MAP  = SENSORS_VAR_MAP

	SENSOR_BME680 = SENSOR_BME680
	SENSOR_BH1750 = SENSOR_BH1750




	'''
	=======================================================
	IRM Object constructor
	=======================================================
	'''
	def __init__(self, wdt = True, DEBUG = 0):
		self.__initSensorSR()
		self.DEBUG = DEBUG
		self.ERRORS = ERRORS
		self.setStationNumber(STATION_NUMBER)

		self.__ui = ui() # IRM Hardware-related user interface (LED and Push-Button)
		# self.pushThread = threading.Thread(target = self.__ui.longPressReboot, args = [], name = 'PushCheckRebootThread')
		# self.pushThread.setDaemon(True)
		# self.pushThread.start()
		os.system('python ui.py &')

		# IRM Mutexes to avoid multiple access tries from different threads
		self.bme680Mutex = Mutex(autoExec = True, DEBUG = False) 
		#self.bh1750Mutex = Mutex(autoExec = False)

		self.bme = BME680.BME680_METEO(DEBUG = False)
		self.bh  = BH1750.BH1750_METEO()

		self.bme.bmeInit()
		self.bh.initBH1750()

		

		self.__mqttRxMsgQueue = [] # IRM Incoming messages will be queued here
		self.__initMQTTClient()


		if wdt is not False:
			self.__launchWDT()
		

	'''
	=======================================================
	IRM Object destructor
	=======================================================
	'''
	def __del__(self):

		#IRM Kill running threads
		for i in self.samplingThread:
			if i.isAlive():
				if self.DEBUG:
					print 'Killing ' + i.getName()
				del i

		# IRM Turn LED off to show service was killed
		self.__ui.output(self.__ui.led, 0)
		del self.__ui

		

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

	def __launchWDT(self):
		myNodeID = STATION_NUMBER
		aliveBeaconPeriod = KEEP_ALIVE_BEACON_PERIOD
		brokerAddr = MQTT_BROKER
		brokerPort = MQTT_PORT

		a = os.system('python wdt.py ' + str(myNodeID) + ' ' + str(aliveBeaconPeriod) + ' ' + str(brokerAddr) + ' ' + str(brokerPort))

		if self.DEBUG:
			print 'Launching WDT'


	'''
	IRM MQTT-related private methods
	'''

	# IRM Connects to MQTT Broker as client
	def __setupMQTTClient(self, address, port):
		self.mqttC = mqttClient.Client()

		self.mqttC.on_message = self.__mqttCallback_onMessage
		self.mqttC.on_connect = self.__mqttCallback_onConnect
		self.mqttC.on_publish = self.__mqttCallback_onPublish

		try:
			self.mqttC.connect(address, port)
		except socket.error:
			if self.DEBUG:
				print 'Could not connect to Mosquitto broker at ' + str(address) + ':' + str(port)
				print 'Restarting service and trying to reconnect...'

			os.system("sudo service mosquitto restart")
			time.sleep(1)
			self.mqttC.reconnect()


	# IRM Subscribes to a determined topic using a determined QoS (QoS = 2 default)
	def __mqttSubscribe(self, topic, qos = 2):
		self.mqttC.subscribe(topic, qos)
		self.mqttThread = threading.Thread(target = self.mqttC.loop_forever, name = 'MQTT Subscriber')
		self.mqttThread.start()


	# IRM Initializes MQTT Client according to this project's requirements
	def __initMQTTClient(self):
		broker = MQTT_BROKER
		port   = MQTT_PORT


		# IRM Init MQTT Client (susbscriber)
		self.__setupMQTTClient(broker, port)


		# IRM Subscribe to every "settings" sub-topic available
		settingsTopic = ROOT_TOPIC + '/' + str(self.getStationNumber()) + '/' + SETTINGS_TOPIC + '/' + MQTT_MULTI_LEVEL
		self.__mqttSubscribe(settingsTopic)

		# IRM "Keep Alive" beacon
		self.keepAliveTopic = ROOT_TOPIC + '/' + KEEP_ALIVE_TOPIC
		keepAliveThread = threading.Thread(target = self.__mqttPublishKeepAlive, args = [KEEP_ALIVE_BEACON_PERIOD])
		keepAliveThread.start()

	# IRM Invoke one-shot publish to MQTT default broker
	def __mqttPublish(self, topic, data):
		self.mqttC.publish(topic = topic, payload = data, qos = 2)

	# IRM Keep alive beacon, should be invoked using a thread, as this is a blocking method
	def __mqttPublishKeepAlive(self, period):
		while True:
			# IRM Keep-alive beacon only contains self station number
			self.__mqttPublish(self.keepAliveTopic, self.getStationNumber())
			if self.DEBUG:
				print "I'm alive!"

			time.sleep(period) # IRM Wait for a determined time until next beacon

	# IRM Append ('Topic','Data') to Rx Queue
	def __mqttMsgQueueAppend(self, data): 
		data = (str(data[0]), data[1])
		self.__mqttRxMsgQueue.append(data)
		if self.DEBUG:
			print data

	def __mqttMsgQueueSupervisor(self):
		while True:
			if len(self.__mqttRxMsgQueue) > 0:
				queuePop = self.__mqttRxMsgQueue.pop(0)
				self.__mqttParseRxMessage(queuePop) # IRM Pop and parse first element in queue
				if self.DEBUG:
					print 'Queue popped: ' + str(queuePop)
			time.sleep(MQTT_RX_QUEUE_SUPERVISE_PERIOD)

	# IRM MQTT Received message via a subscribed topic callback
	def __mqttCallback_onMessage(self, mqttc, obj, msg): 
		self.__mqttMsgQueueAppend( (msg.topic, msg.payload) )

	# IRM MQTT Successful connection callback
	def __mqttCallback_onConnect(self, mqttc, obj, flags, rc):

		# IRM Start supervising MQTT RX Queue. If something arrives, parse it immediately
		mqttQueueSupervisorThread = threading.Thread(target = self.__mqttMsgQueueSupervisor)
		mqttQueueSupervisorThread.start()

		self.samplingThread = range(len(self.SENSOR_NAMES))

		# IRM Launch periodic sampling of connected sensors
		for i in range(len(self.SENSOR_NAMES)):
		#for i in [TEMP]:
			sensor = self.SENSOR_NAMES[i]
			self.samplingThread[i] = threading.Thread(target = self.periodicSampler, args = [sensor], name = str(sensor) + ' periodic sampler')
			self.samplingThread[i].setDaemon(True)
			self.samplingThread[i].start()
			if self.DEBUG:
				print 'Launching thread: ' + str(i)

		# IRM Turn LED on to show MQTT was successful
		self.__ui.output(self.__ui.led, 1)

		if self.DEBUG:
			print 'Connected! rc: ' + str(rc)

	# IRM MQTT Published callback
	def __mqttCallback_onPublish(self, mqttc, obj, mid):
		if self.DEBUG:
			print 'Published! mid: ' + str(mid)




	# IRM Parse received message and execute corresponding action
	# As initial subscription discards messages with <stationNumber>
	# which differ with self <stationNumber>, topic discrimination
	# will start from /Settings sub-topic
	def __mqttParseRxMessage(self, data):
		# IRM Topic example: METEO/<stationNumber>/Settings/SamplingRate/<sensor>
		topic   = data[0]
		payload = data[1]

		if SETTINGS_TOPIC in topic: # IRM Is this a config message from GUI?
			topic = str(topic.split('/'+ SETTINGS_TOPIC +'/')[1]) # IRM <operation>/<sensor>

			if self.DEBUG:
				print 'Partially parsed topic: ' + topic

			if SR_TOPIC in topic: # IRM is this a Sampling Rate config order from GUI?
				sensor = str(topic.split(SR_TOPIC + '/')[1]) # IRM Which sensor should I modify?
				if sensor in SENSOR_TOPICS_R:
					sensorName = SENSOR_TOPICS_R[sensor]
					newSR  = int(payload) # IRM Sampling Rate in seconds

					
					ok = self.setSR(sensorName, newSR)

					if self.DEBUG:
						print 'New Sampling Rate for ' + sensor + ': ' + str(newSR) + ' seconds'
						print 'Sampling rates: ' + str(self.getSRvalues())


					return ok
				else:
					if self.DEBUG:
						print 'Invalid sensor name/topic: ' + str(sensor)
						return ERRORS[INVALID_SENSOR_NAME]

	# IRM Publish formatted sensor data to MQTT Topic
	def __mqttPublishSensorValue(self, sensorName, value):
		topic = ROOT_TOPIC + '/' + str(self.getStationNumber()) + '/' + DATA_TOPIC + '/' + SENSOR_TOPICS[sensorName]


		if self.DEBUG:
			print '__mqttPublishSensorValue --- ' + str(topic) + ' : ' + str(value)

		for i in value:
			self.__mqttPublish(topic, i)



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
				if self.DEBUG:
					print 'Invalid sampling rate (SR): ' + str(interval) + ' seconds'
					print 'SR must be between [' + str(minSR) + ',' + str(maxSR) + ']'
				return self.ERRORS[INVALID_SAMPLING_RATE] # IRM Invalid sampling rate
					
		else:
			if self.DEBUG:
				print 'Sensor "' + sensor + '" not valid.'
				print 'Sensor name must be one of the following in the list' + str(sensorNames)
			
			return self.ERRORS[INVALID_SENSOR_NAME] # IRM	

		return 0 # IRM No errors during operation

	def getSensorNames(self):
		return self.SENSOR_NAMES

	def getSensorMap(self):
		return self.SENSORS_MAP

	def getSRvalues(self): #IRM Sampling rate values for each sensor
		return self.__SR

	def getStationNumber(self):
		return self.stationNumber

	def setStationNumber(self, n = 0):
		if type(n) == int:
			if n >= 0:
				self.stationNumber = n
		else:
			return self.ERRORS[INVALID_STATION_NUMBER]

	'''
	IRM Other public methods
	'''

	# IRM Periodic sensor sampling method. Must be invoked from a separate thread
	def periodicSampler(self, sensorName):
		while True:
			sensorValue = self.sampleSensor(sensorName)

			if self.DEBUG:
				print 'Periodic sampler received this sample: ' + str(sensorValue)

			ok = sensorValue[0]
			if ok == True:
				value = sensorValue[1]

				# IRM Publish sensor value to MQTT Topic
				self.__mqttPublishSensorValue(sensorName, value)

			sleepInterval = self.getSRvalues()[sensorName]
			time.sleep(sleepInterval)


	# IRM Sample a determined variable in one-shot mode
	def sampleSensor(self, sensorName):
		if sensorName in self.getSensorNames():
			sMap = self.getSensorMap()
			if sMap[sensorName] == self.SENSOR_BME680:
			# IRM Measure with BME680_METEO class


				if sensorName == TEMP:
					sample = self.bme680Mutex.lock(self.bme.sampleTemperature, [])

					if sample is not False:
						return (True, [sample])
					else:
						return (False, [self.ERRORS[INVALID_TEMP_VALUE]])


				elif sensorName == HUM:
					sample = self.bme680Mutex.lock(self.bme.sampleHumidity, [])

					if sample is not False:
						return (True, [sample])
					else:
						return (False, [self.ERRORS[INVALID_HUM_VALUE]])


				elif sensorName == PRES:
					sample = self.bme680Mutex.lock(self.bme.samplePressure, [])

					if sample is not False:
						return (True, [sample])
					else:
						return (False, [self.ERRORS[INVALID_PRES_VALUE]])


				elif sensorName == AIR_Q:
					sample = self.bme680Mutex.lock(self.bme.sampleAirQuality, [])

					if sample is not False:
						return (True, [sample])
					else:
						return (False, [self.ERRORS[INVALID_AIR_Q_VALUE]])


				elif sensorName == PPM:
					sample = self.bme680Mutex.lock(self.bme.samplePPM, [])

					if sample is not False:
						return (True, [sample])
					else:
						return (False, [self.ERRORS[INVALID_PPM_VALUE]])


				else:
					return (False, [self.ERRORS[INVALID_SENSOR_NAME]])


			elif sMap[sensorName] == self.SENSOR_BH1750:
			# IRM Measure with BH1750_METEO class

				# IRM Sensor data return format:
				# (Successful measurement, [List with measurements])
				# Successful measurement : True False
				# List with measurements: 
				# If successful : List with measurements
				# If unsuccessful : List with a single element containing error code

				light = self.bh.bh1750MeasureLight()
				if light is not False:
					return (True, [light])
				else:
					return (False, [self.ERRORS[INVALID_LIGHT_VALUE]])

			else:
				return (False, self.ERRORS[INVALID_SENSOR_NAME])
		else:
			return (False, self.ERRORS[INVALID_SENSOR_NAME])



def meteoTestBench():
	try:
		myMeteo = Meteo(True) # IRM Enable Debugging
		#myMeteo = Meteo(False) # IRM Debugging disabled
	except KeyboardInterrupt:
		print 'Killing Meteo!'
		del myMeteo


if __name__ == '__main__':
	meteoTestBench()

