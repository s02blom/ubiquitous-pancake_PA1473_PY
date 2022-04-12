#!/usr/bin/env pybricks-micropython
# from typing_extensions import runtime
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import (Motor, TouchSensor, ColorSensor,
                                 InfraredSensor, UltrasonicSensor, GyroSensor)
from pybricks.parameters import Port, Stop, Direction, Button, Color
from pybricks.tools import wait, StopWatch, DataLog
from pybricks.robotics import DriveBase
from pybricks.media.ev3dev import SoundFile, ImageFile
import time


# This program requires LEGO EV3 MicroPython v2.0 or higher.
# Click "Open user guide" on the EV3 extension tab for more information.


# Create your objects here.
ev3 = EV3Brick()

#Motor definitions
Left_drive = Motor(Port.C)
Right_drive = Motor(Port.B)
Crane_motor = Motor(Port.A)
#Saknar en robot drivebase. Betyder att vin the kan köra robit.run och köra båda motorerna samtidigt.

#Sensor definitions
touch_sencor = TouchSensor(Port.S1)
colour_sensor = ColorSensor(Port.S3)
ultrasonic_sensor = UltrasonicSensor(Port.S4)

robot = DriveBase(Left_drive, Right_drive, wheel_diameter=55.6,axle_track=104) #SB. Stämmer wheel och axle för robotten vi har just nu?

# Constants
LINE_REFLECTION = 4
OFF_LINE_REFLECTION = 60

threshold = (LINE_REFLECTION + OFF_LINE_REFLECTION) / 2

DRIVE_SPEED = 75

TURN_RATE_AMPLIFIER = 3

#Here is where you code starts

def driveForward() -> None:
    deviation = colour_sensor.reflection() - threshold
    turn_rate = TURN_RATE_AMPLIFIER * deviation
    robot.drive(DRIVE_SPEED, turn_rate)

while(True):
    #Kod för att följa linje
    driveForward()
    