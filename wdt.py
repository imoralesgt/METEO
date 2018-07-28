import os
import sys
import time
import socket
import threading
import paho.mqtt.client as mqttClient

from defs import * #IRM Global Definitions

class WDT(object):

	REQUIRED_PARAMETERS = 5 # IRM ['scriptName.py', 'nodeID', 'aliveTimeout', 'serverIP', 'serverPort']
	MAX_ALIVE_PERIODS   = 3 # IRM Max alive periods without beacon to execute WDT action (restart service)

	MQTT_ROOT_TOPIC  = ROOT_TOPIC
	MQTT_ALIVE_TOPIC = KEEP_ALIVE_TOPIC
	ALIVE_TOPIC      = MQTT_ROOT_TOPIC + '/' + MQTT_ALIVE_TOPIC


	def __init__(self, args, debug = False): # IRM 'args' will be retreived from sys.argv
		self.DEBUG = debug
		self.args = args

		self.nodeID = False
		self.aliveTimeout = False
		self.serverIP = False
		self.serverPort = False
		self.wdtRunning = False
		self.msgFlag = False # IRM An ALIVE Beacon Arrived!


		if self.parseArguments() is not True:
			if self.DEBUG:
				print "Couldn't parse arguments!"
			return False

		self.mqttC = mqttClient.Client()
		self.mqttC.on_message = self.__mqttCallback_onMessage
		self.mqttC.on_connect = self.__mqttCallback_onConnect
		self.mqttC.on_publish = self.__mqttCallback_onPublish

		try:
			
			self.mqttC.connect(self.serverIP, self.serverPort) #IRM Connect to broker to listen to 'ALIVE' beacons
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
		mqttThread.setDaemon(True)
		mqttThread.start()


	'''
	IRM Private methods encapsulation
	'''


	'''
	IRM MQTT-Related Methods
	'''		
	def __mqttCallback_onMessage(self, mqttc, obj, msg):
		if self.DEBUG:
				print 'Message arrived to WDT service: (' + str(msg.topic) + ':' + str(msg.payload) + ')'
		if msg.topic == self.ALIVE_TOPIC:

			try:
				node = int(msg.payload)
				if node == self.nodeID:
					self.setMsgFlag()
					
			except TypeError:
				if self.DEBUG:
					print 'Type Error on MSG' + str(msg)
				pass		

	def __mqttCallback_onConnect(self, mqttc, obj, flags, rc):
		if self.DEBUG:
			print 'Connection to broker successful'
		self.msgFlag = False
		self.wdtRunning = False
		self.mqttC.subscribe(self.ALIVE_TOPIC)
		if self.DEBUG:
			print 'Subscribed to "' + str(self.ALIVE_TOPIC) + '" topic'


	def __mqttCallback_onPublish(self, mqttc, obj, mid):
		if self.DEBUG:
			print 'Message published! MID ' + mid



	'''
	IRM Setters and getters
	'''

	def setMsgFlag(self):
		self.msgFlag = True

	def clearMsgFlag(self):
		self.msgFlag = False

	def getMsgFlag(self):
		return self.msgFlag

	def getArguments(self):
		return self.args


	def parseArguments(self):
		args = self.getArguments()

		if len(args) != self.REQUIRED_PARAMETERS:
			if self.DEBUG:
				print 'Error! --- ' + str(self.REQUIRED_PARAMETERS) + ' are required. ' + str(len(args)) + ' received!'
			return False

		try:
			self.nodeID = int(args[1])
			self.aliveTimeout = int(args[2])
			self.serverIP = str(args[3])
			self.serverPort = str(args[4])
			if self.DEBUG:
				print 'Parameters ok! --- ' + str(args)
				print 'serverIP type: ' + str(type(self.serverIP))
				print 'serverPort type: ' + str(type(self.serverPort))
			return True
		except:
			if self.DEBUG:
				print 'Wrong arguments:  ' + str(args)
			return False

	

	def checkWDT(self, currentTime): #IRM Returns True if a WDT restart is mandatory
		if currentTime - self.startTime > self.aliveTimeout * self.MAX_ALIVE_PERIODS:
			return True

		return False

	def restartMETEO(self): #IRM Restart METEO execution 
		a = os.system('sudo pkill meteo')
		a = os.system('./meteo.py &')

	def wdt(self):
		if self.wdtRunning is True:
			restart = self.checkWDT(time.time())
			if restart is True:
				if self.DEBUG:
					print 'WDT Activated! No alive beacons received'

				self.restartMETEO()
				self.wdtRunning = False
				self.startTime  = False

			if self.getMsgFlag() is True:
				self.startTime = time.time()
				self.clearMsgFlag()
				if self.DEBUG:
					print 'ALIVE beacon received while WDT running. Restarting counter...'

			time.sleep(1)

		else:
			if self.getMsgFlag() is True:
				self.startTime = time.time()
				self.wdtRunning = True

				if self.DEBUG:
					print 'First ALIVE beacon received! Starting WDT now!'
		time.sleep(0.01)



def main():
	arguments = sys.argv
	meteoWDT = WDT(args = arguments, debug = False)
	while True:
		meteoWDT.wdt()


if __name__ == '__main__':
	main()

