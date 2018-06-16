import bme680 #Based on Pimoroni's BME680 Python Wrapper
import time 

class BME680_METEO(object):

	def __init__(self, DEBUG = 0):
		
		self.DEBUG = DEBUG
		self.temp = 'TEMPERATURE'
		self.hum  = 'HUMIDITY'
		self.pres = 'PRESSURE'
		self.gas  = 'GAS'

		self.bme = bme680.BME680()

		if self.DEBUG: #IRM Print out calibration DATA if Debug mode is enabled
			print("Calibration data:")

			for name in dir(self.bme.calibration_data):
					if not name.startswith('_'):
						value = getattr(self.bme.calibration_data, name)

						if isinstance(value, int):
							print("{}: {}".format(name,value))




	def bmeInit(self): #IRM Initialize BME680 with default sampling settings
		self.bme.set_humidity_oversample(bme680.OS_2X)
		self.bme.set_pressure_oversample(bme680.OS_4X)
		self.bme.set_temperature_oversample(bme680.OS_8X)
		self.bme.set_filter(bme680.FILTER_SIZE_3)
		self.bme.set_gas_status(bme680.ENABLE_GAS_MEAS) #IRM Enable gas resistance measurement for air-quality data

		if self.DEBUG:
			print '\n\nInitial reading:'
			for name in dir(self.bme.data):
				value = getattr(self.bme.data, name)

			if not name.startswith('_'):
				print("{}: {}".format(name, value))

		#IRM Setup gas heater profile 
		self.bme.set_gas_heater_temperature(320)
		self.bme.set_gas_heater_duration(150)
		self.bme.select_gas_heater_profile(0)

	def getSensorObject(self):
		return self.bme

	#IRM Return BME680 measurements. Gas measurment will be done only when heater is ready
	def getSensorData(self, temp = True, hum = True, pres = True, gas = True):
		sensor = self.getSensorObject()
		sensorData = {}

		if sensor.get_sensor_data():
			if temp:
				sensorData[self.temp] = float('{:.2f}'.format(sensor.data.temperature))

			if hum:
				sensorData[self.hum]  = float('{:.1f}'.format(sensor.data.humidity))

			if pres:
				sensorData[self.pres] = float('{:.1f}'.format(sensor.data.pressure))

			if gas:
				#IRM Measure gas resistance only if heater is stable and measurements are valid
				if sensor.data.heat_stable:
					sensorData[self.gas] = int('{:.0f}'.format(sensor.data.gas_resistance))

		return sensorData



if __name__ == '__main__':
	sensorAmbiental = BME680_METEO(True)
	sensorAmbiental.bmeInit()

	try:
		while True:
			print sensorAmbiental.getSensorData()
			time.sleep(1)
	
	except KeyboardInterrupt:
		print 'Finalizada lectura BME680'
