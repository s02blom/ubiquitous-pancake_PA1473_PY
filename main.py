#!/usr/bin/env pybricks-micropython
# from typing_extensions import runtime
from pybricks.hubs import EV3Brick
from pybricks.ev3devices import (Motor, TouchSensor, ColorSensor,
                                 InfraredSensor, UltrasonicSensor, GyroSensor)
from pybricks.parameters import Port, Stop, Direction, Button, Color
from pybricks.tools import wait, StopWatch, DataLog
from pybricks.robotics import DriveBase
from pybricks.media.ev3dev import SoundFile, ImageFile
from pybricks.messaging import BluetoothMailboxClient,TextMailbox
import time
import _thread

# This program requires LEGO EV3 MicroPython v2.0 or higher.
# Click "Open user guide" on the EV3 extension tab for more information.

# Create your objects here.
ev3 = EV3Brick()

#Motor definitions
Left_drive = Motor(Port.C, positive_direction=Direction.COUNTERCLOCKWISE)
Right_drive = Motor(Port.B, positive_direction=Direction.COUNTERCLOCKWISE)
Crane_motor = Motor(Port.A)

#Sensor definitions
touch_sensor = TouchSensor(Port.S1)
colour_sensor = ColorSensor(Port.S3)
ultrasonic_sensor = UltrasonicSensor(Port.S4)

robot = DriveBase(Left_drive, Right_drive, wheel_diameter=47, axle_track=128) #SB. Stämmer wheel och axle för roboten vi har just nu?

# Constants
LINE_REFLECTION = 67
OFF_LINE_REFLECTION = 84

threshold = (LINE_REFLECTION + OFF_LINE_REFLECTION) / 2

DRIVE_SPEED = 75
DRIVE_WITH_PALLET = 50
CRANE_SPEED = 200
STOP_DISTANCE = 350
PALET_DISTANCE = 500

DESIRED_TURN_RATE = 45
TURN_RATE_AMPLIFIER = DESIRED_TURN_RATE / ((OFF_LINE_REFLECTION - LINE_REFLECTION) / 2)

GROUND_LIFT_ANGLE = 50

driving_with_pallet = False

#Colour
brown_warehouse = Color.BROWN
red_warehouse = Color.RED
blue_warehouse = Color.BLUE
green_to_pickup_and_deliver = Color.GREEN
olive_for_center_circle = 0
purple_in_deliver = 0

COLORS = {
    "red": (75,25,38),
    "blue": (11,27,48),
    "yellow line": (57,49,11),
    "Brown": (14,9,12),
    "Black": (3,3,2),
    "Purple": (14,12,47),
    "Middle Circle": (17,19,13),
    "Green": (10,44,21),
    "White": (71,86,100)
}

#Here is where you code starts
def print_on_screen(text):
    ev3.screen.clear()
    ev3.screen.print(str(text))

def select_color():
    color = input("Please select a color? ")
    return color

def print_on_screen(text):
    ev3.screen.clear()
    ev3.screen.print(str(text))

def classify_color(rgb_in):
    OFFSET = 5
    match_r = []
    match_g = []
    match_b = []
    r_in, g_in, b_in = rgb_in
    for color_key in COLORS.keys():
        r, g, b = COLORS[color_key]
        if r_in < (r + OFFSET) and r_in > (r - OFFSET):
            match_r.append(color_key)
        if g_in < (g + OFFSET) and g_in > (g - OFFSET):
            match_g.append(color_key)
        if b_in < (b + OFFSET) and b_in > (b - OFFSET):
            match_b.append(color_key)
    matches = []
    for color_key in COLORS.keys():
        if color_key in match_r and color_key in match_g and color_key in match_b:
            matches.append(color_key)
    if len(matches) == 0:
        return None
    return matches

def select_path(path_color):
    # print_on_screen(f'Seachring for {path_color} path.')
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
    # print_on_screen(f'Driving to {path_color} warehouse.')
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
    print_on_screen('Returning to the circle.')
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

def drive_forward(precise = True) -> None:
    deviation = max(LINE_REFLECTION, colour_sensor.reflection()) - threshold
    turn_rate = TURN_RATE_AMPLIFIER * deviation
    drive_speed = 75
    if driving_with_pallet == True:
        drive_speed = 40
    if precise:
        # speed = drive_speed / (0.8 + abs(deviation) * 0.06)
        speed = drive_speed * max(0.1, 1 - (abs(turn_rate) / DESIRED_TURN_RATE))
    else:
        speed = drive_speed
    robot.drive(speed, turn_rate)

def follow_color(color_rgb):
    drive_speed = 75
    if driving_with_pallet == True:
        drive_speed = 40
    turn_rate = 45
    if color_rgb == classify_color(colour_sensor.rgb())[0]:
        turn_rate = -25
    robot.drive(drive_speed, turn_rate)

def find_pallet(is_pallet_on_ground: bool) -> None:
    print_on_screen('Searching for a pallet.')
    """
    Antagande:
    Vi står i varuhuset
    Resultat:
    Vi är redo att köra pickup pallet, med eller utan höjd
    """
    # count = 0
    # drive forward
    #  while pallet not found and count <2:
   
    
    #
    #   if warehouse.red
    #      turn 90 degrees left
    #   else if warehouse.blue
    #      turn 90 degrees right
    #   drive until yellow line found
    #   turn back
    #   count++
    count = 0

    while ultrasonic_sensor.distance() > PALET_DISTANCE and count < 2:
        
        robot.turn(90)
        #robot.straight(150)
        while colour_sensor.color() != COLORS["yellow line"]:
            drive_forward()
        robot.turn(-90)
        count = count + 1
        #Sväng 90 vänster
        #Kör en bil längd
        #Sväng 90 höger
        #Loop

    if is_pallet_on_ground:
        pick_up_pallet_on_ground()
    elif(is_pallet_on_ground == False):#elif 
        #pick_up
        pick_up_pallet_in_air()
    #drive back to entrance
    while(count > 0):
        #Sväng åt rätt riktning.
        while colour_sensor.color() != COLORS["yellow line"]:
            drive_forward()
        count = count - 1

def pick_up_pallet_in_air() -> None:
    Crane_motor.run_angle(CRANE_SPEED, 200)
    pick_up_pallet_on_ground()
    Crane_motor.run_angle(-CRANE_SPEED, 200)

def pick_up_pallet_on_ground() -> None:
    print_on_screen('Picking up the found pallet.')
    """
    Antagande:
    En pallet har redan hittats och 
    Vi står med nosen pekande på den
    Resultat:
    Palleten är upplockad
    Vi har backat tillbacka till start position. 
    """
    is_pallet_on_properly = False
    drive_speed_crawl = 60
    stop_after_time = 6 #If the time to pick up the item exceeds 3 seconds the pick-up will fail.
    drive_forward_time = time.perf_counter()
    robot.reset()
    
    while(not is_pallet_on_properly and (time.perf_counter() -drive_forward_time) <stop_after_time):
        is_pallet_on_properly = touch_sensor.pressed()
        robot.drive(drive_speed_crawl, 0)
    drive_forward_stop_time = time.perf_counter()
    robot.drive(0, 0)
    if not is_pallet_on_properly:
        print("Picking up failed.")
    else:
        print("picking up")
        Crane_motor.run_angle(-CRANE_SPEED, GROUND_LIFT_ANGLE)
        driving_with_pallet = True
    time_to_back_out = drive_forward_stop_time -  drive_forward_time
    distance_to_back_out = (time_to_back_out * drive_speed_crawl) /1000 #(ms *mm/s)/m
    distance_to_back_out = robot.distance()
    robot.straight(-distance_to_back_out)    
    #Sväng om?
def reset_crane():
    Crane_motor.run_until_stalled(CRANE_SPEED)

# Main thread for driving etc
def main():
    while(True): 
        print(colour_sensor.rgb())
        
def get_color(color = "svart"):
    while (True):
        color = input("Choose color... ")
        if str(color).lower() == "red":
            print(color)
        elif str(color).lower() == "blue":
            print(color)
        else:
            print("No color matching input")


_thread.start_new_thread(main,(),)
_thread.start_new_thread(get_color,(),)

while True:
    pass
