import smbus
import time

from BH1750 import BH1750
from sensorDefs import *

class BH1750_METEO(object):

	DEFAULT_SENSITIVITY = DEFAULT_LIGHT_SENSITIVITY
	DEFAULT_I2C_ADDRESS = DEFAULT_LIGHT_I2C_ADDRESS

	def __init__(self, address = DEFAULT_I2C_ADDRESS, smBus = 1):

		self.i2cBus = smbus.SMBus(smBus)
		self.address = address
		

		self.sensorOk = True



	def initBH1750(self):
		try:
			self.lightSensor = BH1750(self.i2cBus, self.address)
			return True

		except IOError:
			print "Can't initialize BH1750 at I2C Address 0x" + '{0:02x}'.format(self.address)
			self.sensorOk = False
			return False

	
	def getSensitivity(self):
		return self.lightSensor.mtreg

	def setSensitivity(self, value):
		if self.sensorOk:
			self.lightSensor.set_sensitivity(value)

	def bh1750MeasureLight(self, sensitivity = DEFAULT_SENSITIVITY):
		try:
			if self.sensorOk:
				self.setSensitivity(sensitivity)
				return float('{0:.1f}'.format(self.lightSensor.measure_high_res2()))

		except IOError:
			print 'BH1750 not found at I2C Address 0x' + '{0:02x}'.format(self.address)
			print 'Stopping measurements...'
			self.sensorOk = False
			return False

		except NameError:
			print "BH1750 sensor couldn't be found! No further measurements can be done..."
			return False


if __name__ == '__main__':

	bh = BH1750_METEO()

	valid = bh.initBH1750()

	while valid:
		lightValue = bh.bh1750MeasureLight()
		if lightValue:
			print str(lightValue) + ' lux'
			time.sleep(1)
		else:
			valid = False






