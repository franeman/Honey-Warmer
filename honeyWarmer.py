# Controller for honey warmer

# Import needed libraries
from time import sleep # Get the sleep command from the time library
import RPi.GPIO as GPIO # Import the RPi.GPIO library for interfacing with GPIO
import dht11 # Import the library to interface with the dht11
import paho.mqtt.client # Import the client mqtt library in paho

# Custom functions

def convertCToF(temp): # Convert temperature from Celcius to Farenheit
    temp = (temp * (9/5)) + 32
    return temp

def readDHT(dht): # Reads from the DHT11 until it gets a valid read
    result = dht.read() # Read from the DHT11
    while (result.error_code != 0): # If there is an error, repeat every second until there is no error
        sleep(1)
        result = dht.read()
    return result # Return the result
    
def readDHT(dht, mqtt): # Reads from the DHT11 until it gets a valid read, then publishes reading to MQTT
    result = dht.read() # Read from the DHT11
    while (result.error_code != 0): # If there is an error, repeat every second until there is no error
        sleep(1)
        result = dht.read()
    temp = convertCToF(result.temperature) # Convert to F
    mqtt.publish("/dht/temp", temp) # Publish temperature reading in F
    mqtt.publish("/dht/humidity", result.humidity) # Publish humidity reading
    return result # Return the result

class Hysteresis: # A class that defines a boolean value with hysteresis
    def __init__(self, setPoint1, setPoint2, inverted=0):
        self.setPoint1 = setPoint1 # The value needed to be passed in order to initially change the result
        self.setPoint2 = setPoint2 # The value needed to fall below in order to change the result back
        result = inverted
        passedPoint1 = 0
    
    def testVal(self, val):
        if (val >= setPoint1 and not passedPoint1): # Value is passing the first set point
            result = not result
            passedPoint1 = 1
        elif (val <= setPoint2 and passedPoint1): # Value fell below the second set point
            result = not result
            passedPoint1 = 0
        return result

# Setup MQTT
mqtt = paho.mqtt.client.Client() # Create a MQTT client object named mqtt
mqtt.username_pw_set("testUser","testUser") # Set the username as testUser with password testUser to log into the MQTT server
mqtt.connect("127.0.0.1") # Connect to the MQTT broker hosted locally on the Pi
mqtt.publish("/debug", "Honey warmer connected!") # Publish connected message to /debug topic

# Configure GPIO
GPIO.setmode(GPIO.BCM) # Use GPIO numbering scheme (use GPIO.BOARD for physical pin numbering)
plate1 = 2 # Plate 1 is GPIO2 (physical pin 3)
plate2 = 3 # Plate 2 is GPIO3 (physical pin 5)
GPIO.setup(plate1, GPIO.OUT, initial=GPIO.LOW) # Set plate1 as an output
GPIO.setup(plate2, GPIO.OUT, initial=GPIO.LOW) # Set plate2 as an output

# Configure DHT11
dataPin = 26 # DHT11 data pin is connected to GPIO19 (physical pin 37)
dht11 = dht11.DHT11(dataPin) # Create an instance of the DHT11 class called dht11 who's signal pin is dataPin

targetTemp = 105 # Target temp to keep the honey at in F
tolerance = 5 # Allowable differnce from target temp
error = 0 # Initial default error value
twoPlateError = 10 # The temperature difference great enough to use 2 heat plates (degrees F)
freq = 5 # Time between measurements
runTwoPlates = Hysteresis(targetTemp-twoPlateError, targetTemp-twoPlateError-tolerance, 1)
runOnePlate = Hysteresis(targetTemp, targetTemp-tolerance, 1)
# Begin main loop
while (True): # Run forever
    result = readDHT(dht11, mqtt) # Read the temp and humidity, publish reading to MQTT
    temp = convertCToF(result.temperature) # Calculate the temperature in degrees F
    if (runTwoPlates.testVal(temp): # If the temp needs to be raised quickly, run both heaters
        GPIO.output(plate1, GPIO.HIGH)
        GPIO.output(plate2, GPIO.HIGH)
    elif (runOnePlate.testVal(temp): # If the temp is close, run 1 heater 
        GPIO.output(plate1, GPIO.HIGH)
        GPIO.output(plate2, GPIO.LOW)
    else: # Temp is in tolerance, turn off the heaters
        GPIO.output(plate1, GPIO.LOW)
        GPIO.output(plate2, GPIO.LOW)
    sleep(freq) # Wait to take the next measurement

