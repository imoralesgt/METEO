import bme680 #IRM Based on Pimoroni's BME680 Python Wrapper

import threading #IRM Non-blocking gas sensor burn-in thread
import time #IRM Sleep and not-that-accurate time measurement

from sensorDefs import * #IRM Sensors-related constants

class BME680_METEO(object):

	'''
	=======================================================
	IMR Class-related globals
	=======================================================	
	'''


	'''
	IRM Private globals
	'''

	__temp = 'TEMPERATURE'
	__hum  = 'HUMIDITY'
	__pres = 'PRESSURE'
	__gas  = 'GAS'


	#IRM Gas sensor burn-in time before it becomes operative
	__GAS_BURN_IN_TIME = GAS_BURN_IN_TIME


	#IRM Gas sensor's heater settings
	__GAS_HEATER_TEMPERATURE = GAS_HEATER_TEMPERATURE
	__GAS_HEATER_DURATION    = GAS_HEATER_DURATION
	__GAS_HEATER_PROFILE     = GAS_HEATER_PROFILE



	'''
	=======================================================
	IRM Object constructor
	=======================================================
	'''

	def __init__(self, DEBUG = 0):
		
		#IRM How many measurements used to compute gas baseline
		if(GAS_BASELINE_MEASUREMENTS > self.__GAS_BURN_IN_TIME):
			self.__GAS_BASELINE_MEASUREMENTS = self.__GAS_BURN_IN_TIME
		else:
			self.__GAS_BASELINE_MEASUREMENTS = GAS_BASELINE_MEASUREMENTS

		self.__HUM_BASELINE = HUM_BASELINE #IRM Ideal indoor relative humidity


		self.__DEBUG = DEBUG

		if DEBUG:
			print 'Gas sensor burn-in time (seconds): ' + str(self.__GAS_BURN_IN_TIME)
			print 'Gas sensor baseline measurements (seconds): ' + str(self.__GAS_BASELINE_MEASUREMENTS)
			print 'Ideal indoor relative humidity (%): ' + str(self.__HUM_BASELINE)
 

		self.bme = bme680.BME680()

		self.__gasReadable = False #IRM Gas sensor status. True until burn-in time reached
		self.__burnInData = [] #IRM Burn-in data used to set the average gas resistance value

		self.__gasBaseLine = 0 #IRM Gas resistance baseline value after burn-in process ended

		if self.__DEBUG: #IRM Print out calibration DATA if Debug mode is enabled
			print("Calibration data:")

			for name in dir(self.bme.calibration_data):
					if not name.startswith('_'):
						value = getattr(self.bme.calibration_data, name)

						if isinstance(value, int):
							print("{}: {}".format(name,value))

	'''
	=======================================================
	IRM Private methods encapsulation
	=======================================================
	'''

	'''
	IRM Setters and Getters
	'''

	def __getGasState(self):
		return self.__gasReadable

	def __setGasState(self, readable):
		if(type(readable) == bool):
			self.__gasReadable = readable
		else:
			self.__gasReadable = False

	'''
	IRM Other private methods
	'''

	def __clearBurnInData(self):
		self.__burnInData = []

	#IRM Must NOT allow high-level access to gas sensor burn-in process
	def __gasBurnIn(self, burnInTime): #IRM Initialize Gas Sensor in a non-blocking action
		startTime = time.time()
		currentTime = time.time()

		self.__clearBurnInData()

		if self.__DEBUG:
			print 'Gas sensor burn-in process running in background...  ' + str(self.__GAS_BURN_IN_TIME) + ' seconds'



		while currentTime - startTime < burnInTime:
			currentTime = time.time()
			if self.bme.get_sensor_data and self.bme.data.heat_stable:
				gas = int(self.bme.data.gas_resistance)
				self.__burnInData.append(gas)
				time.sleep(1)

				if self.__DEBUG:
					print 'Gas sensor burn-in process running... (' \
					 + str(int(currentTime - startTime)) + ' out of ' + str(burnInTime) + ' seconds passed'

		#IRM After burn-in time has been reached, set 'gasReadable' as True
		if self.__DEBUG:
			print 'Gas sensor is ready!'

		self.__setGasState(True)

		#IRM Also, set the gas baseline value for further measurements
		gasBaseLine = sum(self.__burnInData[-self.__GAS_BASELINE_MEASUREMENTS:]) / float(self.__GAS_BASELINE_MEASUREMENTS)
		self.setBaseLineValue(gasBaseLine)

		if self.__DEBUG:
			print 'Gas baseline value: ' + str(self.getBaseLineValue())

	'''
	=======================================================
	IRM Public Methods
	=======================================================
	'''

	'''
	IRM Setters and Getters
	'''
	def getBaseLineValue(self):
		return self.__gasBaseLine

	def setBaseLineValue(self, value):
		try:
			self.__gasBaseLine = value
		
		except TypeError:
			self.__gasBaseLine = 0
			print 'Invalid Gas Baseline Value Type. Must be an Int/Float'
			print 'Argument type: ' + str(type(value))


	'''
	IRM Other publich methods
	'''

	def killBurnInDaemon(self):
		if self.burnInThread.isAlive(): #IRM Is burn-in thread still running?
			del self.burnInThread
			return True

		return False #IRM Ok, I didn't do anything anyways. Suicide thread has killed itself before I arrived.


	def bmeInit(self): #IRM Initialize BME680 with default sampling settings
		self.bme.set_humidity_oversample(bme680.OS_2X)
		self.bme.set_pressure_oversample(bme680.OS_4X)
		self.bme.set_temperature_oversample(bme680.OS_8X)
		self.bme.set_filter(bme680.FILTER_SIZE_3)
		self.bme.set_gas_status(bme680.ENABLE_GAS_MEAS) #IRM Enable gas resistance measurement for air-quality data

		if self.__DEBUG:
			print '\n\nInitial reading:'
			for name in dir(self.bme.data):
				value = getattr(self.bme.data, name)

			if not name.startswith('_'):
				print("{}: {}".format(name, value))

		#IRM Setup gas heater profile 
		self.bme.set_gas_heater_temperature(self.__GAS_HEATER_TEMPERATURE)
		self.bme.set_gas_heater_duration(self.__GAS_HEATER_DURATION)
		self.bme.select_gas_heater_profile(self.__GAS_HEATER_PROFILE)

		#IRM Start gas sensor burn-in process in a non-blocking thread
		self.burnInThread = threading.Thread(target = self.__gasBurnIn, args=(self.__GAS_BURN_IN_TIME,), name = 'Gas Sensor Burn-In', )
		self.burnInThread.setDaemon(True) #IRM Run in background
		self.burnInThread.start() #IRM Suicide thread. Will kill itself after burn-in time has concluded

	def getSensorObject(self):
		return self.bme

	#IRM Return BME680 measurements. Gas measurment will be done only when heater is ready
	def getSensorData(self, temp = True, hum = True, pres = True, gas = True):
		sensor = self.getSensorObject()
		sensorData = {}

		if sensor.get_sensor_data():
			if temp:
				sensorData[self.__temp] = float('{:.2f}'.format(sensor.data.temperature))

			if hum:
				sensorData[self.__hum]  = float('{:.1f}'.format(sensor.data.humidity))

			if pres:
				sensorData[self.__pres] = float('{:.1f}'.format(sensor.data.pressure))

			if gas:
				#IRM Measure gas resistance only if heater is stable and measurements are valid
				if sensor.data.heat_stable and self.__getGasState():
					sensorData[self.__gas] = int('{:.0f}'.format(sensor.data.gas_resistance))

		return sensorData



if __name__ == '__main__':
	sensorAmbiental = BME680_METEO(True)
	sensorAmbiental.bmeInit()

	try:
		while True:
			print sensorAmbiental.getSensorData()
			time.sleep(1)
	
	except KeyboardInterrupt:
		print '\n\n'
		if(sensorAmbiental.killBurnInDaemon()):
			print 'Background gas sensor burn-in daemon stopped successfully'
		else:
			print 'No daemons running in background'
		print 'BME680 sampling stopped successfully'
