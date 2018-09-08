import os
import time
import datetime
import socket
import threading
import paho.mqtt.client as mqttClient

import sqlite3

from defs import *

#IRM Used to store data avoiding blank fields in csv registers
#By default 1 minute window, otherwise some fields left in blank
class StorageQueue(object):

	DATE_FIELD  = 'date'
	TIME_FIELD  = 'time'
	NODE_FIELD  = 'node'
	TEMP_FIELD  = TEMP
	HUM_FIELD   = HUM
	PRES_FIELD  = PRES
	LIGHT_FIELD = LIGHT
	AIR_Q_FIELD = AIR_Q

	#IRM CSV Fields Enum
	CSV_FIELDS = {
					DATE_FIELD : 0, TIME_FIELD : 1,
					NODE_FIELD : 2, TEMP_FIELD : 3,
					HUM_FIELD  : 4, PRES_FIELD : 5,
					LIGHT_FIELD: 6, AIR_Q_FIELD: 7
				 }

 	SENSOR_IDX = {
					TEMP_FIELD : 0,
					HUM_FIELD  : 1, PRES_FIELD : 2,
					LIGHT_FIELD: 3, AIR_Q_FIELD: 4
				 }



	SENSORS_SHIFT = 3 #Shift between CSV register and Data register

	DELTA_TIME = 60 #IRM Passed seconds before creating a new register
	

	# IRM A new instance must be created for each CSV file (every new day)
	def __init__(self):
		self.SENSOR_FIELDS = {}
		for i in self.CSV_FIELDS:
			tempField = self.CSV_FIELDS[i] - self.SENSORS_SHIFT
			if tempField >= 0:
				self.SENSOR_FIELDS[i] = tempField

		self.initialize()
	

	def initialize(self):
		#Initialize queues

		self.registerQueue = self.__resetRegisterQueue()

		self.tempQueue = self.__resetQueue()
		self.humQueue  = self.__resetQueue()
		self.presQueue = self.__resetQueue()
		self.lightQueue= self.__resetQueue()
		self.airQQueue = self.__resetQueue()

		self.listOfQueues = [self.tempQueue, self.humQueue, self.presQueue, self.lightQueue, self.airQQueue]


		cnt = 0
		self.whichQueue = {}

		for i in self.SENSOR_FIELDS:
			x = self.SENSOR_FIELDS[i]
			self.whichQueue[cnt] = self.listOfQueues[x]
			cnt += 1

		#IRM Last time data was received for each variable
		self.lastTime = [False] * (len(self.CSV_FIELDS) - self.SENSORS_SHIFT) 

		#IRM Last time a register was available to be writen into CSV file
		self.lastRegisterTime = False

		#IRM Queue ready to be written into CSV file
		self.queueReady = False

		#IRM String-formatted queue
		self.csvQueue = ''

		

	#IRM Create a clean register so data can be stored here
	def __resetRegisterQueue(self, defaultValue = ''):
		queue = []
		for i in range(len(self.CSV_FIELDS)):
			queue.append(defaultValue)
		return queue

	def __resetQueue(self):
		return []

	def __getUnixTime(self):
		return time.time()

	def __getLastTime(self, idx):
		return self.lastTime[idx]

	def __setLastTime(self, idx, time):
		self.lastTime[idx] = time

	def __hasLastTime(self, index):
		return self.lastTime[index] is not False

	def __resetLastTime(self, index):
		self.lastTime[index] = False

	def __avg(self, queue): #IRM Average
		a = 0
		for i in queue:
			a += i

		return a/len(queue)

	def __toRegisterQueue(self, index, queue):
		if self.lastRegisterTime is False: #First row
			self.lastRegisterTime = self.__getUnixTime()
		

		if (self.__getUnixTime() - self.lastRegisterTime < self.DELTA_TIME):
			if len(queue) > 0:
				data = str(self.__avg(queue))
				self.registerQueue[index] = data
				print '__toRegisterQueue: Averaging values before sending'
		else:
			print '__toRegisterQueue: Writing to Register as 1 minute has passed by'
			print '__toRegisterQueue: Register queue:  ' + str(self.registerQueue)
			self.__writeToRegister(self.registerQueue)
			self.lastRegisterTime = self.__getUnixTime()


			


	def __writeToRegister(self, queueData):
		# TODO: Append to CSV file here! (Open -> append -> close) File
		queueData[0] = str(datetime.date.today())
		queueData[1] = str(time.strftime('%H:%M'))
		queueData[2] = str(0)

		print 'Original Queue Data: ' + str(queueData)

		self.csvQueue = ','.join(queueData) #Comma-separated values
		self.queueReady = True

		print 'Register written: ' + str(self.csvQueue)

		self.dbCommit(queueData)
		print '__writeToRegister: Data commited into Database'

		#self.initialize()


	def __duplicateList(self, srcList):
		dstList = []
		for i in srcList:
			dstList.append(i)
		return dstList

			

	def appendValue(self, value, sensorIndex):

		
		'''
		Example of usage (with humidity):

		myStorageQueue = StorageQueue()
		myStorageQueue.appendValue(myHumValue, myStorageQueue.HUM_FIELD)
		'''

		#idx = self.SENSOR_FIELDS[self.TEMP_FIELD] #IRM Temp index
		idx = self.SENSOR_IDX[sensorIndex] #IRM Variable Index (TEMP_FIELD, HUM_FIELD, etc...)

		#queue = self.whichQueue[idx]
		

		if self.__hasLastTime(idx):
			if self.__getUnixTime() - self.__getLastTime(idx) < self.DELTA_TIME:

				print 'appendValue: Value appended to queue!'
				self.whichQueue[idx].append(float(value))
				print 'appendValue: Current queue: ' + str(self.whichQueue[idx])
			else:
				print 'appendValue: Now sending to Register Queue: ' + str(self.whichQueue[idx])
				self.__toRegisterQueue(idx + self.SENSORS_SHIFT, self.whichQueue[idx])
				self.__resetLastTime(idx)

				#IRM Clean current queue
				#self.whichQueue[idx] = self.__resetQueue()
		else:
			print 'appendValue: New value in queue'
			try:
				self.whichQueue[idx] = [float(value)] #IRM Replace 'False' with first value
			except Except as e:
				print 'appendValue: Exception ' + str(e)
			self.__setLastTime(idx, self.__getUnixTime())


			self.__toRegisterQueue(idx + self.SENSORS_SHIFT, self.whichQueue[idx])


			print 'appendValue: Current queue ' + str(self.whichQueue[idx])



	#IRM Return string-formatted register if ready. Otherwise, return False
	def isQueueReady(self):
		if self.queueReady:
			newQueue = self.__duplicateList(self.csvQueue)
			self.initialize()
			return newQueue
		else:
			return False


	#IRM SQLITE3 Database data commit
	def dbCommit(self, data): 
		self.dbFileName  = DB_FILE_NAME
		self.dbTableName = DB_TABLE_NAME
		#self.DB_TABLE_FIELDS = DB_TABLE_FIELDS
		dbConnector = sqlite3.connect(self.dbFileName)
		dbCursor	= dbConnector.cursor()

		#IRM Data parameter must be a tuple/list container with
		#sorted data according to DB's table data fields
		sqlQuery = "INSERT INTO " + str(self.dbTableName) + " values " + str(tuple(data))

		dbCursor.execute(sqlQuery)
		dbConnector.commit()
		dbConnector.close()

		self.dbExportToCSV()

	def dbExportToCSV(self):
		dbFileName  = self.dbFileName
		dbTableName = self.dbTableName
		dbExpExtension = METEO_FILE_FORMAT
		command = 'sqlite3 -header -csv ' + str(dbFileName) + ' "select * from ' + str(dbTableName) + ';" > ' + str(dbTableName) + str(dbExpExtension)
		os.system(command)






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
				print 'Connecting to Broker -> ' + self.serverIP + ':' + str(self.serverPort)


		except socket.error:
			if self.DEBUG:
				print 'Connection to broker failed - restarting Mosquitto service!'
			os.system('sudo service mosquitto restart')
			self.mqttC.reconnect()

		except Exception as e:
			print 'Error: ' + str(e)

		mqttThread = threading.Thread(target = self.mqttC.loop_forever, args = [], name = 'MQTT Loop Thread')
		mqttThread.setDaemon(False)
		mqttThread.start()

		self.stQueue = StorageQueue()


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
				print 'Succesfully sent to storage queue'
		else:
			if self.DEBUG:
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
		except Exception as e:
			if self.DEBUG:
				print 'Exception: ' + str(e)
			return False

		sensorName = str(topic[-1])
		if self.DEBUG:
			print 'Sensor Name: ' + sensorName

		if sensorName not in SENSOR_TOPICS_LST:
			if self.DEBUG:
				print 'Sensor name not in sensor topics list: ' + str(SENSOR_TOPICS_LST)
			return False

		#IRM Send to storage queue (stQueue)
		self.stQueue.appendValue(payload, SENSOR_TOPICS_R[sensorName])
		return True


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

