#!/usr/bin/python3
"""
Name: Kgomotso Welcome
Student Number: WLCKGO001

Name: James Rasekoala
Student Number: RSKJAM001

Project A : Environment Logger
Date: 13 September 2019
"""


import RPi.GPIO as GPIO
import Adafruit_MCP3008
import spidev
import time
import threading
import os
import datetime
import decimal
import numpy as num
from ADCThread import read_Adc

# Import SPI library (for hardware SPI) and MCP3008 library.
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008

import blynklib
import random
BLYNK_AUTH = 'sbLSXvOAsijxmj-AWIn_hNz2MrSns2p8' #Blybk Authincation code
READ_PRINT_MSG = "[READ_VIRTUAL_PIN_EVENT] Pin: V{}"
# initialize blynk
blynk = blynklib.Blynk(BLYNK_AUTH)

# Button Pins
resetPin = 26
intervalPin = 19
stopPin = 13
alarmPin = 6

# Global Variables
values = [0,0,0,0,0,0,0,0]		# Array with values that will be printed
FrequencyIndex = 2	    #Value for indexing interval array 
Frequency = [1,2,5]		#Array to hold frequencies
systemTime = [0,0,0]	#Array to hold the system time
restFlag = False		#Flag to know the resting state
heading = ["RTC Time","Sys Timer","Humidity","Temp","Light","DAC out","Alarm"]		#Array to hold heading
running = True		    #Flag to hold flag for Running or Paused
previousAlarmTime = [0,-3,0]	#Array to hold the Prevoious time. initially set to Negative 3 minutes
CurrentTime = [0,0,0]	#Array to hold current time	
DACoutput = 0	 #Global variable for DAC out
AlarmOnFlag = False		#Flag to hold alarm state
ReadAdcFlag = True 
Adcrunning = False		
PWMBrightness = 0

#values for blynk
humidity = 0 # virtual pin 1
temperature = 0 # virtual pin 2
light = 0 # virtual pin 3

# Pinmode
GPIO.setmode(GPIO.BCM)

# Button Pins IO
GPIO.setup(resetPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(intervalPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(stopPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(alarmPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

GPIO.setup(18,GPIO.OUT) #Setting GPIO 18 as an output for the Alarm
pwm = GPIO.PWM(18,50)	# Initialize PWM on pwmPin 100Hz 
pwm.start(0)
GPIO.setwarnings(False)	 #Setting warning to False
# Hardware SPI configuration:
SPI_PORT   = 0
SPI_DEVICE = 0
mcp = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))

READ_PRINT_MSG = "[READ_VIRTUAL_PIN_EVENT] Pin: V{}"


# register handler for virtual pin V11 reading
@blynk.handle_event('read V11')
def read_virtual_pin_handler(pin):
	#method to write variables to Blynk App
	print(READ_PRINT_MSG.format(11))
	global humidity
	global temperature
	global light
	global AlarmOnFlag
	#writing humidity, temperature and light to blynk
	blynk.virtual_write(11, humidity)	
	blynk.virtual_write(2, temperature)
	blynk.virtual_write(3, light)
	
	if(AlarmOnFlag == True):
		blynk.virtual_write(4, 100)
	else:
		blynk.virtual_write(4, 0)


def RTC_time():
	#Method to read time from RTC
	rtc = time.localtime()
	current_time = time.strftime("%H:%M:%S", rtc)
	return current_time
	
	
def Alarm():
	#Method to control Alarm activites and variables
	global pwm
	global DACoutput
	global CurrentTime
	global previousAlarmTime
	global AlarmOnFlag
	global PWMBrightness
	

	# check for valid alarm only the alarm is off
	if(AlarmOnFlag == False):
		#check the DAC out value for the alarm
		if((DACoutput > 2.65) or (DACoutput < 0.65)):
			# Array to hold difference in current time and Previous alarm
			Answer = [0,0,0] 
			
			# Calculating the difference in time
			for i in range(3):
				Answer[i] = CurrentTime[i]- previousAlarmTime[i]
				
			#checking if the difference is 3 minutes or more
			if(Answer[0]>0):
				AlarmOnFlag = True
				for i in range(3):
					previousAlarmTime[i] = CurrentTime[i]  
			
			if(Answer[1]>=3):
				AlarmOnFlag = True
				for i in range(3):
					previousAlarmTime[i] = CurrentTime[i]
				
			if(Answer[1]*60+Answer[2]>=180):
				AlarmOnFlag = True
				for i in range(3):
					previousAlarmTime[i] = CurrentTime[i]
	
		
	#switching on and off alarm based on flag	
	if(AlarmOnFlag ==True):
		PWMBrightness = PWMBrightness+20
		if (PWMBrightness==100):
			pwm.ChangeDutyCycle(PWMBrightness)
			PWMBrightness = 0
		else:
			pwm.ChangeDutyCycle(PWMBrightness)
	else:
		pwm.ChangeDutyCycle(0)
	
		
def Timer():
	''' Timer method is responsible incementing Current Time and System Time,
	  Ensuring overflow is handled correctly and No overflow for hours and
      Converting time from int to correct printing format     '''
	global systemTime
	global restFlag
	global FrequencyIndex
	global Frequency
	global CurrentTime
	
	currentTime = "" # Varibale to hold the string version of current time
	hourString = ""
	minString = ""
	secString = ""	
	
	#Resting System Time to 00:00:00 and Resting flag
	if restFlag == True:
		restFlag = False
		systemTime[2] = 0
		systemTime[1] = 0
		systemTime[0] = 0
	else:
		secs = systemTime[2]
		mins = systemTime[1]
		hours = systemTime[0]
		
		#incrementing based on the User's interval
		secs = secs+Frequency[FrequencyIndex]	
		
		if secs>60:
			# Control overflow of seconds
			secs = secs-60	#Setting seconds to allowed value
			systemTime[2] = secs
			CurrentTime[2] = secs
			mins = mins + 1	 #Incrementing minutes
		
		#saving seconds
		systemTime[2] = secs	
		CurrentTime[2] = secs	
		
		if mins>60:
			# Control overflow of seconds
			mins = mins-60	#Setting minutes to allowed value
			systemTime[1] = mins
			CurrentTime[1] = mins
			hours = hours + 1	#Incrementing hours
			systemTime[2] = hours
			CurrentTime[2] = hours
			
		#saving seconds	
		systemTime[1] = mins
		CurrentTime[1] = mins
		
	#Converting time from int to correct printing format
	if(systemTime[0]<10):
		hourString = "0"+str(systemTime[0])
	else:
		hourString = str(systemTime[0])
		
	if(systemTime[1]<10):
		minString = "0"+str(systemTime[1])
	else:
		minString = str(systemTime[1])
		
	if(systemTime[2]<10):
		secString = "0"+str(systemTime[2])
	else:
		secString = str(systemTime[2])
			
	#Putting the house time string together
	currentTime = hourString+":"+minString+":"+secString
	return currentTime
	
def Convert(arr):
    #This method is responsible for convering the ADC value's
	#It also updates the global variables humidity, temperature and light
	#The method also updates he array that will be printed  
   
	
	global humidity
	global temperature
	global light
	global DACoutput
	global AlarmOnFlag
	global Adcrunning
	
	#Assigning Values from ADC to variacles
	hum = arr[0]
	Temp = arr[1]
	Lig = arr[2]
	
	#Calutating ADC data to correct values
	hum = 3.3*(hum/1023)
	Temp = ((3.3*(Temp/1023))-0.5)*100
	Lig = 3.3*(Lig/1023)
	
	#Updating Array with calculated variables
	arr[0] = hum
	arr[1] = Temp
	arr[2] = Lig
	arr[3] = (Lig/1023)*hum
	
	#Updating Global variables for Blynk to us
	DACoutput = arr[3]
	humidity = hum
	temperature = Temp
	light = Lig
	
	#Calling Alarm method to Check updated variables
	Alarm()
	if(AlarmOnFlag):
		arr[4] = '*'
	else:
		arr[4] = ' '
		
	#Updating the Rest of the Array for printing
	arr[5] = RTC_time()
	arr[6] = Timer()
	return arr



# Interrupt Method for Rest button
def resetPush(channel):
	global heading
	if (GPIO.input(channel) == GPIO.LOW): # Avoid trigger on button realease
		global restFlag
		restFlag = True	#updating Rest flag 
		os.system('clear') 	#clearing Screen
		print("")
		print("System Reset.")
		print('| {0:>7} | {1:>6} | {2:>5} | {3:>5} | {4:>4} | {5:>4} | {6:>4} |'.format(*heading))



# Interrupt Method for Interval button
def intervalPush(channel):
	global heading
	if (GPIO.input(channel) == GPIO.LOW): # Avoid trigger on button realease
		global Frequency 
		global FrequencyIndex
		FrequencyIndex = FrequencyIndex+1	#incrementing frequency index to change Frequency position
		
		#Statement to control the Frequency index not to go out of array boundary
		if(FrequencyIndex>2):
			FrequencyIndex = 0
		print("")
		print("Interval button pushed.") # DEBUG
		print('| {0:>7} | {1:>6} | {2:>5} | {3:>5} | {4:>4} | {5:>4} | {6:>4} |'.format(*heading))


# Interrupt Method for Stop button
def stopPush(channel):
	
	global heading
	global running
	if (GPIO.input(channel) == GPIO.LOW): # Avoid trigger on button realease

		#Change flag based on current state when button is pressed 
		if(running):
			running = False
			print("Program Stopped.")
		else:
			running = True
			print("Program Started.")
			

# Interrupt Method for Alarm button
def alarmPush(channel):
	global heading
	global AlarmOnFlag
	if (GPIO.input(channel) == GPIO.LOW): # Avoid trigger on button realease
		
		#Only switch off alarm when it is on 
		if(AlarmOnFlag ==True):
			AlarmOnFlag = False
			print("")
			print("Alarm dismissed.")
			print('| {0:>7} | {1:>6} | {2:>5} | {3:>5} | {4:>4} | {5:>4} | {6:>4} |'.format(*heading))

# Interrupt Event Detection
GPIO.add_event_detect(resetPin, GPIO.FALLING, callback=resetPush, bouncetime=100)
GPIO.add_event_detect(intervalPin, GPIO.FALLING, callback=intervalPush, bouncetime=100)
GPIO.add_event_detect(stopPin, GPIO.FALLING, callback=stopPush, bouncetime=100)
GPIO.add_event_detect(alarmPin, GPIO.FALLING, callback=alarmPush, bouncetime=100)
###-------------###

def main():
	global running
	global values
	global ReadAdcFlag
	os.system('clear')
	
	#Setting up channel column headers.
	heading = ["RTC Time","Sys Timer","Humidity","Temp","Light","DAC out","Alarm"]
	print('| {0:>7} | {1:>6} | {2:>5} | {3:>5} | {4:>4} | {5:>4} | {6:>4} |'.format(*heading))
	print('-' * 67)
	# Main program loop.
	while True:
		read_Adc(True) #Thread to read ADC	
		if (running):	# When not stopped
			print('| {5:>7} | {6:>9} | {0:>7.3f}V | {1:>2.0f} C | {2:>5.0f} | {3:>6.2f}V | {4:>5} |'.format(*Convert(values)))
			blynk.run()	# Run Blynk
		else:
			blynk.run()
			Timer()
			Alarm()
		time.sleep(Frequency[FrequencyIndex])	#Pause program based on class interval	


if __name__ == "__main__":
	try:
		main()
	except KeyboardInterrupt:
		print("Exiting gracefully")
		# Turn off your GPIOs here
		pwm.stop()
		GPIO.cleanup() #cleanup previous channel

