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

# Setup MQTT
mqtt = paho.mqtt.client.Client() # Create a MQTT client object named mqtt
mqtt.username_pw_set("testUser","testUser") # Set the username as testUser with password testUser to log into the MQTT server
mqtt.connect("127.0.0.1") # Connect to the MQTT broker hosted locally on the Pi
mqtt.publish("/debug", "Honey warmer connected!") # Publish connected message to /debug topic

# Configure GPIO
GPIO.setmode(GPIO.BCM) # Use GPIO numbering scheme (use GPIO.BOARD for physical pin numbering)
plate1 = 4 # Plate 1 is GPIO4 (physical pin 7)
plate2 = 22 # Plate 2 is GPIO22 (physical pin 15)
fan = 6 # Fan is GPIO6 (physical pin 7)
GPIO.setup(plate1, GPIO.OUT, initial=GPIO.LOW) # Set plate1 as an output
GPIO.setup(plate2, GPIO.OUT, initial=GPIO.LOW) # Set plate2 as an output
GPIO.setup(fan, GPIO.OUT, initial=GPIO.LOW) # Set fan as an output

# Configure DHT11
dataPin = 19 # DHT11 data pin is connected to GPIO19 (physical pin 37)
dht11 = dht11.DHT11(dataPin) # Create an instance of the DHT11 class called dht11 who's signal pin is dataPin

targetTemp = 105 # Target temp to keep the honey at in F
tolerance = 5 # Allowable differnce from target temp
error = 0 # Initial default error value
twoPlateError = 10 # The temperature difference great enough to use 2 heat plates (degrees F)
freq = 5 # Time between measurements
fanOnTemp = 80 # Turn on the fan at 80 F

# Begin main loop
while (True): # Run forever
    result = readDHT(dht11, mqtt) # Read the temp and humidity, publish reading to MQTT
    error = targetTemp - convertCToF(result.temperature) # Calculate the temperature error in degrees F
    if (error > twoPlateError): # If the temp needs to be raised quickly, run both heaters
        GPIO.output(plate1, GPIO.HIGH)
        GPIO.output(plate2, GPIO.HIGH)
    elif (error > tolerance): # If the temp is not in tolerance but is close, run 1 heater 
        GPIO.output(plate1, GPIO.HIGH)
        GPIO.output(plate2, GPIO.LOW)
    else: # Temp is in tolerance, turn off the heaters
        GPIO.output(plate1, GPIO.LOW)
        GPIO.output(plate2, GPIO.LOW)
    if (result.temperature >= fanOnTemp): # If the temp is above the fan turn on set point
        GPIO.output(fan, GPIO.HIGH) 
    else: # The fan is below the turn on set point
        GPIO.output(fan, GPIO.LOW)
    sleep(freq) # Wait to take the next measurement

