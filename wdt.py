import os
import sys
import time
import socket
import paho.mqtt.client as mqttClient

from defs import * #IRM Global Definitions

class WDT(object):


	REQUIRED_PARAMETERS = 5 # IRM ['scriptName.py', 'nodeID', 'aliveTimeout', 'serverIP', 'serverPort']
	MAX_ALIVE_PERIODS   = 10 # IRM Max alive periods without beacon to restart service

	MQTT_ROOT_TOPIC  = ROOT_TOPIC
	MQTT_ALIVE_TOPIC = KEEP_ALIVE_TOPIC
	ALIVE_TOPIC      = MQTT_ROOT_TOPIC + '/' + MQTT_ALIVE_TOPIC


	def __init__(self, args, debug = False): # IRM 'args' will be retreived from sys.argv
		self.mqttC = mqttClient.Client()
		self.mqttC.on_message = self.__mqttCallback_onMessage
		self.mqttC.on_connect = self.__mqttCallback_onConnect
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

		try:
			if self.DEBUG:
				print 'Broker: ' + self.serverIP + ':' + self.serverPort

			self.mqttC.connect(self.serverIP, self.serverPort) #IRM Connect to broker to listen to 'ALIVE' beacons
		except socket.error:
			os.system('sudo service mosquitto restart')
			self.mqttC.reconnect()

		while True:
			self.wdt()



	'''
	IRM Private methods encapsulation
	'''


	'''
	IRM MQTT-Related Methods
	'''		
	def __mqttCallback_onMessage(self, mqttc, obj, msg):
		if msg.topic == self.MQTT_ALIVE_TOPIC:
			try:
				node = int(msg.payload)
				if node == self.nodeID:
					self.setMsgFlag()
					
			except TypeError:
				if DEBUG:
					print 'Type Error on MSG' + str(msg)
				pass		

	def __mqttCallback_onConnect(self, mqttc, obj, flags, rc):
		mqttC.subscribe(MQTT_ALIVE_TOPIC)


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
		a = os.system('sudo pkill meteo.py')
		a = os.system('python meteo.py &')

	def wdt(self):
		if self.getMsgFlag() is True:
			restart = False
			self.clearMsgFlag()
			if self.wdtRunning is not True:
				self.startTime = time.time()
				self.wdtRunning = True
			else:
				restart = self.checkWDT(time.time())

			if restart is True:
				self.restartMETEO()
				self.wdtRunning = False
				self.startTime = False



def main():
	arguments = sys.argv
	meteoWDT = WDT(args = arguments, debug = True)


if __name__ == '__main__':
	main()

