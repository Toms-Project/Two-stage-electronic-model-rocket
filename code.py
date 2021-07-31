## flight program
import storage
import time
import board
import busio
import digitalio
import adafruit_lis3dh ## importing library for acelerometer
import pulseio

switch = digitalio.DigitalInOut(board.GP26)
switch.switch_to_input(pull=digitalio.Pull.DOWN)
## defining a switch added to the board later on, which when activated, will prevent the computer from writing to the flash memory on the pico
## but will allow the pico to write.  This is necessary, as the pico can only ever be written to from one source at a time, in order to prevent corruption.
## I need to do this, in order to allow the pico to save a file, containing the flight data from the accelerometer. 
storage.remount("/", switch.value)## this bit takes the input from the switch and actually changes the read-write permissions.
led = digitalio.DigitalInOut(board.GP25)
led.direction = digitalio.Direction.OUTPUT## this defines an led at a controllable address, built into the pico. I use this to show a user what stage the program is at, as it obviously has no screen.
servo = pulseio.PWMOut(board.GP14, frequency=50)## this defines a servo, controllable via PWM, which I will use to deploy the parachute.
SDA=board.GP20
SCL=board.GP21
i2c = busio.I2C(SCL, SDA)
lis3dh = adafruit_lis3dh.LIS3DH_I2C(i2c)
## that last bit sets up the accelerometer to communicate via an I2C protocol, whcih uses two wires; a system clock line, which syncs the two units, and a system data line, where the actual serial data is sent. 
igniter1 = digitalio.DigitalInOut(board.GP17)
igniter1.direction = digitalio.Direction.OUTPUT
igniter1.value = False
igniter2 = digitalio.DigitalInOut(board.GP16)
igniter2.direction = digitalio.Direction.OUTPUT
igniter2.value = False
## defines the output pins which are connected to the 'gate' pinon the mosfets and essentially controls their state. When these pins are 'True', they send a voltage (3.3v) to the mosfets, and they turn os.
launchdetect = digitalio.DigitalInOut(board.GP27)
launchdetect.switch_to_input(pull=digitalio.Pull.DOWN)
## sets the launch detect switch to a certain pin, and addsa pull down resistor built into the board which ensures there are no false positives from static build up.
servo.duty_cycle = 3000

def flight():
    with open("flight_data", "a") as file:
        igniter1.value = 1## lights first stage engine
        file.write("launch\n")## tells the flight data file when launch was
        for i in range(45):
            led.value = 1
            time.sleep(0.05)
            led.value = 0
            time.sleep(0.05)
            x,y,z = lis3dh.acceleration## prints flight data to file, along with its time-stamp, and oreintation in the rocket.
            file.write(str((x))+ "up/down(m/s/s) , " + str((y)) + "left/right(m/s/s) , " + str((z)) + "front/back(m/s/s) @ " + str(i/10)+ "s \n")
        igniter1.value = 0
        igniter2.value = 1## fires second stage engine, and disengages the first
        redundancy = 0
        g = 0
        file.write("second stage\n")
        while True:
            time.sleep(0.01)
            redundancy = redundancy + 0.01
            g = g + 1
            x,y,z = lis3dh.acceleration
            if g == 10:
                g = 0
                file.write(str((x)) + "up/down(m/s/s) , " + str((y)) + "left/right(m/s/s) , " + str((z)) + "front/back(m/s/s) @ " + str((redundancy)+4.4) + "s \n")
            x = round(x,-1)## Since it is very unlikely the vertical acceleration is ever going to be truly 0, it is rounded to the nearest 10. 
            if x == 0 or redundancy > 8:## if the accelerometer reports back that there is no longer any vertical acelleration, then the parachute is deployed, and flight data is saved, along with a 'parachute' message.
                file.write("parachute\n")## if the acceleromter were to fail / does not do as I expect, then after 8 seconds the parachute is fired anyway.
                servo.duty_cycle = 8500
                time.sleep(1)
                servo.duty_cycle = 3000
                file.close()
                igniter2.value = 0
                while True:
                    led.value = 0
                    time.sleep(0.25)
                    led.value = 1
                    time.sleep(0.25)

b=0                
while True:
    if launchdetect.value == 1: ## this bit detects the state of the launch switch, and if it is high, over the full course of 100 clock cycles, turns on the flight program, triggering launch. 
        b = b + 1
    elif launchdetect.value == 0:## if no launch is detected, the computer stays in pad-idle mode, and blinks its led, to tell you this.
        b = 0
        led.value = 1
        time.sleep(0.25)
        led.value = 0
        time.sleep(0.25)
    if b == 100:
        b = 0
        flight()
            

        