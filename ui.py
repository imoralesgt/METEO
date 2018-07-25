import RPi.GPIO as GPIO
import time


# IRM Physical User Interface
# LED and Push-Button interaction
class UI_METEO(object):

	gpio = GPIO

	# IRM Setup GPIO directives
	def __init__(self, ledPin = 11, pushPin = 7):

		self.led  = ledPin
		self.push = pushPin

		#IRM set pin numbering mode
		self.gpio.setmode(self.gpio.BOARD)



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

	def input(self, inPin):
		return self.gpio.input(inPin)

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






def main():
	print 'Starting UI Test - LED Blinking'
	ui = UI_METEO()
	x = bool(0)
	for i in range(10):
		ui.output(ui.led, x)
		time.sleep(0.5)
		x = not x
	print 'UI Test Done! - LED Blinking'






if __name__ == '__main__':
	main()