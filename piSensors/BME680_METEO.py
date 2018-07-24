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
	IRM 'Private' globals
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

	#IRM IAQ-related constants
	__IAQ_MAX_GAS = IAQ_MAX_GAS # IRM Max gas resistance value
	__IAQ_MIN_GAS = IAQ_MIN_GAS # IRM Min gas resistance value
	__IAQ_MIN_HUM = IAQ_MIN_HUM # IRM Min relative humidity
	__IAQ_MAX_HUM = IAQ_MAX_HUM # IRM Max relative humidity
	__IAQ_OPT_HUM = HUM_BASELINE # IRM Optimal relative humidity
	__IAQ_OPT_GAS = GAS_OPTIMAL  # IRM Optimza gas resistance

	__IAQ_HUM_CONTRIBUTION = IAQ_HUM_CONTRIBUTION
	__IAQ_GAS_CONTRIBUTION = IAQ_GAS_CONTRIBUTION



	'''
	=======================================================
	IRM Object constructor
	=======================================================
	'''

	def __init__(self, DEBUG = False):
		
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

		self.sensorData = {}

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

	# IRM Must NOT allow high-level access to gas sensor burn-in process
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
					 + str(int(currentTime - startTime)) + ' out of ' + str(burnInTime) + ' seconds passed)'

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
	IRM Other public methods
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
	def getSensorData(self, temp = False, hum = False, pres = False, gas = False):
		sensor = self.getSensorObject()

		if sensor.get_sensor_data():

			if temp:
				self.sensorData[self.__temp] = float('{:.2f}'.format(sensor.data.temperature))

			if hum:
				self.sensorData[self.__hum]  = float('{:.1f}'.format(sensor.data.humidity))

			if pres:
				self.sensorData[self.__pres] = float('{:.1f}'.format(sensor.data.pressure))

			if gas:
				#IRM Measure gas resistance only if heater is stable and measurements are valid
				if sensor.data.heat_stable and self.__getGasState():
					self.sensorData[self.__gas] = int('{:.0f}'.format(sensor.data.gas_resistance))
				else:
					self.sensorData[self.__gas] = False

		return self.sensorData

	def sampleTemperature(self):
		sample = self.getSensorData(temp = True)
		if self.__temp in sample:
			return sample[self.__temp]
		return False

	def sampleHumidity(self):
		sample = self.getSensorData(hum = True)
		if self.__hum in sample:
			return sample[self.__hum]
		return False

	def samplePressure(self):
		sample = self.getSensorData(pres = True)
		if self.__pres in sample:
			return sample[self.__pres]
		return False

	def sampleAirQuality(self):
		sample = self.getSensorData(hum = True, gas = True)
		# IRM ToDo: Compute Air Quality (%) using Humidity and Gas measurements ===========================
		if self.__hum in sample and self.__gas in sample and sample[self.__gas] is not False: #IRM If gas burn-in time has ended
			return self.computeIAQ(sample[self.__hum], sample[self.__gas], temp = False)
		return False

	def samplePPM(self):
		sample = self.getSensorData(gas = True)
		gasBaseLine = self.getBaseLineValue()
		#IRM ToDo: Compute PPM using Gas Baseline and Gas measurements ====================================
		if self.__gas in sample and sample[self.__gas] is not False:
			# IRM At the moment, using PPM as raw gas resistance measurement for debugging purposes
			return sample[self.__gas]
		return False

	# IRM Arduino-like implementation of MAP function
	def map(self, x, iL, iH, oL, oH):
		return (x - iL) * (oH - oL) / float(iH - iL) + oL


	# IRM Compute Index of Air Quality based on raw measurements (humidity, gas resistance and optionally temperature)
	def computeIAQ(self, hum, gas, temp = False):
		humContrib = self.__IAQ_HUM_CONTRIBUTION
		gasContrib = self.__IAQ_GAS_CONTRIBUTION

		optimalHum = self.__IAQ_OPT_HUM
		optimalGas = self.__IAQ_OPT_GAS

		minHum = self.__IAQ_MIN_HUM
		minGas = self.__IAQ_MIN_GAS

		maxHum = self.__IAQ_MAX_HUM
		maxGas = self.__IAQ_MAX_GAS

		if self.__DEBUG:
			print 'IAQ Computation'
			print 'Humidity       (0% - 100%) ------ ' + str(hum)
			print 'Gas Resistance (50R - 50000R) --- ' + str(gas)

		# IRM Humidity contribution computation
		if hum < optimalHum: # IRM If humidity is less than 40%
			humContrib = humContrib * (1 - (optimalHum - hum) / float(optimalHum))
		else: 
			humContrib = humContrib * (1 -  (hum - optimalHum) / float(maxHum - optimalHum))

		if self.__DEBUG:
			print 'Humidity contribution: ' + str(humContrib)

		if gas < minGas:
			gas = minGas

		if gas > maxGas:
			gas = maxGas

		# IRM Gas resistance computation
		gasContrib = (self.map(gas, minGas, maxGas, 0, 1)) * gasContrib

		if self.__DEBUG:
			print 'Gas resistance contribution: ' + str(gasContrib)

		if(temp is not False): # IRM if temperature is required for computation
			pass # IRM Not implemented yet

		iaq = humContrib + gasContrib
		iaq = 500.0 * (1 - iaq) # IRM IAQ Computation in a 0 to 500 basis. 0 is the best
		iaq = int(iaq)

		return iaq




if __name__ == '__main__':
	sensorAmbiental = BME680_METEO(True)
	sensorAmbiental.bmeInit()

	try:
		while True:
			print sensorAmbiental.getSensorData(True, True, True, True)
			time.sleep(1)
	
	except KeyboardInterrupt:
		print '\n\n'
		if(sensorAmbiental.killBurnInDaemon()):
			print 'Background gas sensor burn-in daemon stopped successfully'
		else:
			print 'No daemons running in background'
		print 'BME680 sampling stopped successfully'
