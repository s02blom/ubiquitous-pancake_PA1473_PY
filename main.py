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
Left_drive = Motor(Port.C, positive_direction=Direction.COUNTERCLOCKWISE)
Right_drive = Motor(Port.B, positive_direction=Direction.COUNTERCLOCKWISE)
Crane_motor = Motor(Port.A)
#Saknar en robot drivebase. Betyder att vin the kan köra robit.run och köra båda motorerna samtidigt.

#Sensor definitions
touch_sensor = TouchSensor(Port.S1)
colour_sensor = ColorSensor(Port.S3)
ultrasonic_sensor = UltrasonicSensor(Port.S4)

robot = DriveBase(Left_drive, Right_drive, wheel_diameter=47, axle_track=128) #SB. Stämmer wheel och axle för roboten vi har just nu?

# Constants
LINE_REFLECTION = 60
OFF_LINE_REFLECTION = 80

threshold = (LINE_REFLECTION + OFF_LINE_REFLECTION) / 2

DRIVE_SPEED = 75
DRIVE_WITH_PALLET = 50
CRANE_SPEED = 50

TURN_RATE_AMPLIFIER = 3

GROUND_LIFT_ANGLE = 200

#Colour
brown_warehouse = 0
red_warehouse = 0
blue_warehouse = 0
green_to_pickup_and_deliver = 0
olive_for_center_circle = 0
purple_in_deliver = 0

#Here is where you code starts

def select_path(path_color):
    """
    Antagande:
    Trucken befinner sig på den gula mutt-ringen.
    Resultat:
    Trucken hittar vägen av önskad färg och svänger mot den.
    """
    while colour_sensor.color() != path_color:
        drive_forward()
    align_left()
    
def drive_to_destination():
    """
    Antagande:
    Trucken har hittat önskad väg och är justerad efter dess riktning.
    Resultat:
    Trucken kör tills den når den svarta ytan vid slutet av vägen.
    """
    while colour_sensor.color() != Color.BLACK:
        drive_forward(precise = True)
    robot.drive(0, 0)

def return_to_circle():
    """
    Antagande:
    Trucken står på den svarta ytan i ett lager med nosen innåt i lagret.
    Resultat:
    Trucken svänger ut och kör tillbaka till mitt-cirkeln.
    """
    while colour_sensor.color() != Color.YELLOW:
        if colour_sensor.color() == Color.BLACK:
            robot.drive(0, 45)
            wait(3000)
        else:
            drive_forward(precise = True)
    align_left()

def align_left():
    robot.drive(0, -45)
    wait(2100)
    robot.drive(0, 0)

def drive_forward(precise = False) -> None:
    deviation = colour_sensor.reflection() - threshold
    turn_rate = TURN_RATE_AMPLIFIER * deviation
    if precise:
        speed = DRIVE_SPEED / (0.8 + abs(deviation) * 0.06)
    else:
        speed = DRIVE_SPEED
    robot.drive(speed, turn_rate)

def pick_up_pallet_on_ground() -> None:
    """
    Antagande:
    En pallet har redan hittats och 
    Vi står med nosen pekande på den
    Resultat:
    Palleten är upplockad
    Vi har backat tillbacka till start position. 
    """
    is_pallet_on_properly = False
    drive_speed_crawl = 30
    stop_after_time = 3000 #If the time to pick up the item exceeds 3 seconds the pick-up will fail.
    drive_forward_time = time.perf_counter()
    
    while(not is_pallet_on_properly and (time.perf_counter -drive_forward_time) <stop_after_time):
        is_pallet_on_properly = touch_sensor.pressed()
        robot.drive(drive_speed_crawl)
    drive_forward_stop_time = time.perf_counter()
    if not is_pallet_on_properly:
        print("Picking up failed.")
    else:
        Crane_motor.run_angle(CRANE_SPEED, GROUND_LIFT_ANGLE)
    time_to_back_out = drive_forward_stop_time -  drive_forward_time
    distance_to_back_out = (time_to_back_out * drive_speed_crawl) /1000 #(ms *mm/s)/m    
    robot.straight(distance_to_back_out)    
    #Sväng om?

while(True):
    #Kod för att följa linje
    drive_forward()
    