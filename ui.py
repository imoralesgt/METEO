import RPi.GPIO as GPIO
import time
import os


# IRM Physical User Interface
# LED and Push-Button interaction
class UI_METEO(object):

	gpio = GPIO
	LONG_PRESS = 30

	# IRM Setup GPIO directives
	def __init__(self, ledPin = 11, pushPin = 7):

		self.led  = ledPin
		self.push = pushPin

		self.ledState = 0

		#IRM set pin numbering mode
		self.gpio.setmode(self.gpio.BOARD)
		self.gpio.setwarnings(False)



		#IRM set I/O directions

		#IRM Push button : input pull-up
		self.gpio.setup(pushPin, self.gpio.IN, pull_up_down = self.gpio.PUD_UP)

		#IRM LED : output
		self.gpio.setup(ledPin, self.gpio.OUT)

	#IRM Cleanup on object destruction
	def __del__(self):
		self.gpio.cleanup()

	def output(self, outPin, value):
		self.gpio.output(outPin, value)
		if outPin == self.led:
			self.ledState = value

	def input(self, inPin):
		return self.gpio.input(inPin)

	def pushPressed(self):
		return not self.gpio.input(self.push)

	# IRM Blocking method. Must be called from a thread if non-blocking operation is desired
	def longPressReboot(self):
		while True:
			ledInitialValue = self.ledState
			push = self.pushPressed()
			if(push):
				startTime = time.time()
				reboot = False
				while push:
					currentTime = time.time()
					self.output(self.led, not self.ledState)
					time.sleep(0.1)
					if currentTime - startTime > self.LONG_PRESS and reboot == False:
						#a = os.system('sudo echo "Rebooting now!"')
						a = os.system('sudo reboot now')
						reboot = True
					push = self.pushPressed()
				self.output(self.led, ledInitialValue)



	# IRM Blocking method. Must be called from a thread if non-blocking operation is desired
	def blink(self, outPin, period, runs = False):
		status = bool(0)

		if runs is not False:
			while(True):
				outPin = status
				status = not status
				time.sleep(period)
		elif type(runs) is int or type(runs) is long:
			for i in range(runs):
				outPin = status
				status = not status
				time.sleep(period)



def test():
	print 'Starting UI Test - LED Blinking'
	ui = UI_METEO()
	x = bool(0)
	for i in range(5):
		ui.output(ui.led, x)
		time.sleep(0.5)
		x = not x
	print 'UI Test Done! - LED Blinking'

	ui.longPressReboot()


def main():
	ui = UI_METEO()
	ui.longPressReboot()


if __name__ == '__main__':
	main()

