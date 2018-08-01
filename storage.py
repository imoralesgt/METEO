import os
import time
import socket
import threading
import paho.mqtt.client as mqttClient

from defs import *

# IRM Storage will be operative only in main METEO Station (Station ID = 0)
# Otherwise, won't be launched from main 'meteo.py'
class Storage(object):

	def __init__(self, DEBUG = 0):

		#IRM METEO Station ID
		self.meteoID = STATION_NUMBER

		if self.meteoID is not 0:
			return False

		self.serverIP = '127.0.0.1' #IRM Storage only available in Main METEO
									#Which corresponds to localhost (127.0.0.1)

		self.serverPort = MQTT_PORT #IRM Just in case broker not listening at default port

		#IRM getting constants from 'defs.py' definitions file
		self.METEO_FILENAME_ROOT = METEO_FILENAME_ROOT
		self.METEO_FILE_FORMAT   = METEO_FILE_FORMAT
		self.METEO_DATA_FOLDER   = METEO_DATA_FOLDER

		self.DEBUG = DEBUG



		#IRM CSV header 
		self.CSV_HEADER = CSV_HEADER

		#IRM MQTT Client
		self.mqttC = mqttClient.Client()
		self.mqttC.on_message = self.__mqttCallback_onMessage
		self.mqttC.on_connect = self.__mqttCallback_onConnect
		self.mqttC.on_publish = self.__mqttCallback_onPublish

		try:
			
			self.mqttC.connect(self.serverIP, self.serverPort) #IRM Connect to broker to listen to data
			if self.DEBUG:
				print 'Connecting to Broker -> ' + self.serverIP + ':' + self.serverPort


		except socket.error:
			if self.DEBUG:
				print 'Connection to broker failed - restarting Mosquitto service!'
			os.system('sudo service mosquitto restart')
			self.mqttC.reconnect()

		except:
			print 'Unknown error!'

		mqttThread = threading.Thread(target = self.mqttC.loop_forever, args = [], name = 'MQTT Loop Thread')
		mqttThread.setDaemon(False)
		mqttThread.start()


	def __getMyID(self):
		return self.meteoID

	def __getCSVHeader(self):
		return self.CSV_HEADER

	#IRM Return today's data file name
	def __getTodayFileName(self):
		return self.METEO_FILENAME_ROOT + '_' + str(self.__getMyID()) + '_' + self.getToday() + self.METEO_FILE_FORMAT

	#IRM Compute whole path + file name based on file name
	def __getDatafileWithPath(self, fileName):
		return self.METEO_DATA_FOLDER + '/' + fileName

	def __getMqttGlobalDataTopic(self):
		#IRM ie. 'METEO/+/Data/#'
		return ROOT_TOPIC + '/' + MQTT_SINGLE_LEVEL + '/' + DATA_TOPIC + '/' + MQTT_MULTI_LEVEL



	#IRM Return today's date in METEO-compatible format
	def getToday(self):
		today = os.popen('date +%Y-%m-%d').rstrip('\n').rstrip('\r').split('-')
		today = ''.join(today)
		return today

	#IRM Returns current time in [HH, MM, SS] format (list type)
	def getTime(self):
		now = time.strftime('%H:%M:%S', time.localtime())
		now = now.split(':')
		if DEBUG:
			print 'Current time: ' + str(now)
		return now

	'''
	IRM MQTT Event-triggered methods
	'''

	def __mqttCallback_onMessage(self, mqttc, obj, msg):
		if self.DEBUG:
				print 'Message arrived to storage service: (' + str(msg.topic) + ':' + str(msg.payload) + ')'

		if self.__praseAndStoreData(msg.topic, msg.payload):
			if self.DEBUG:
				print 'Succesfully stored data'
			else:
				print 'Could not store data'


	#IRM If connection to broker successful...
	def __mqttCallback_onConnect(self, mqttc, obj, flags, rc):
		if self.DEBUG:
			print 'Connection to broker successful'

		# IRM Connect to each data message topic (from any METEO Station)
		globalDataTopic = self.__getMqttGlobalDataTopic()
		self.mqttC.subscribe(globalDataTopic)
		if self.DEBUG:
			print 'Subscribed to global data topic: "' + globalDataTopic + '"'

	# IRM Not intended to be used by now...
	def __mqttCallback_onPublish(self, mqttc, obj, mid):
		if self.DEBUG:
			print 'Message published! MID ' + mid




	#IRM Create an unexisting file.
	#Path must be included in fileName
	#Header format is a comma-separated string with CSV columns
	def __createDataFile(self, fileName, header):
		# IRM Create (and replace if already exists) a new file
		newFile = open(fileName, 'w')
		newFile.write(header + '\n')
		newFile.close()

	#IRM Does 'fileName' data file already exist?
	def __datafileExists(self, fileName):
		path = fileName
		return os.path.isfile(path)


	#IRM Use this method to append data. Don't worry about dates!
	#Just take care of sending the filename in appropiate format (use __getTodayFileName method)
	#If file doesn't exist, it will be created automatically every day
	def __appendToFile(self, fileName, data):
		# IRM Create file if doesn't exist yet
		if not self.__datafileExists(fileName):
			self.__createDataFile(fileName, self.__getCSVHeader())

		# IRM Append data to existing file
		dataFile = open(fileName, 'a')
		dataFile.write(data + '\n')
		dataFile.close()

	def __praseAndStoreData(self, topic, payload):
		topic = topic.split('/')
		if len(topic) != 4:
			return False

		try:
			stationNumber = int(topic[1])
		except TypeError:
			if self.DEBUG:
				print 'Invalid station number: ' + str(topic[1])
				return False

		sensorName = str(topic[-1])
		if self.DEBUG:
			print 'Sensor Name: ' + sensorName

		if sensorName not in SENSOR_TOPICS_LST:
			if self.DEBUG:
				print 'Sensor name not in sensor topics list: ' + str(SENSOR_TOPICS_LST)
			return False




	'''
	TODO:
		- [ ] Retreive data from Broker and add it to CSV file (running in parallel thread?)
		- [ ] Create a new file every day
		- [ ] If several measurements from different sensors retreived within the same MINUTE,
		      store them in the same CSV row
		- [ ] If several measurements form the same sensor retreived within the same MINUTE,
			  average the value and then store it
	'''




def main():
	meteoStorage = Storage(DEBUG = True)
	while True:
		pass

if __name__ == '__main__':
	main()

