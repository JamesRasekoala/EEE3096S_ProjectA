import threading
import time
import RPi.GPIO as GPIO

# Import SPI library (for hardware SPI) and MCP3008 library.
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008

values = [0,0,0,0,0,0,0,0]
resetPin = 26
readBool = True
# Hardware SPI configuration:
SPI_PORT   = 0
SPI_DEVICE = 0
mcp = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))

def resetPush(channel):
	global heading
	if (GPIO.input(channel) == GPIO.LOW): # Avoid trigger on button realease
		print("Reset button pressed.")
		
def setup():
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(resetPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.add_event_detect(resetPin, GPIO.FALLING, callback=resetPush, bouncetime=100)
	#Contains all code for initialisation of RPi.GPIO
	print("setup")
	
def fetch_sensor_vals(sensor_pin):
	for i in range(5):  #for i in range(3):
		GPIO.input(sensor_pin)
		time.sleep(0.2)

def read_Adc(readBool1):
	global mcp
	global values
	global readBool
	for i in range(4):
		# The read_adc function will get the value of the specified channel (0-7).
		values[i] = mcp.read_adc(i) # update global variable as reading happens
		time.sleep(0.2)	#To slow down number of times the thread reads the ADC 
	readBool = False

if __name__ == "__main__":
	setup()
	# Create a thread to call the function and pass "12" in as sensor pin
	x = threading.Thread(target=read_Adc, args=(True,))
	print("Starting thread")
	x.start()
	print("Waiting for the thread to finish")
	x.join()
	print("Reading finished")
