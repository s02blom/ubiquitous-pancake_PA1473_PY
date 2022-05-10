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

# Creatimg EV3Brick Object
ev3 = EV3Brick()

# Motor definitions
Left_drive = Motor(Port.C, positive_direction=Direction.COUNTERCLOCKWISE)
Right_drive = Motor(Port.B, positive_direction=Direction.COUNTERCLOCKWISE)
Crane_motor = Motor(Port.A)

# Sensor definitions
touch_sensor = TouchSensor(Port.S1)
colour_sensor = ColorSensor(Port.S3)
ultrasonic_sensor = UltrasonicSensor(Port.S4)

# Robot definition
robot = DriveBase(Left_drive, Right_drive, wheel_diameter=47, axle_track=128) #SB. Stämmer wheel och axle för roboten vi har just nu?

# drive_forward constants
# LINE_REFLECTION = 67
# OFF_LINE_REFLECTION = 84
# threshold = (LINE_REFLECTION + OFF_LINE_REFLECTION) / 2
# DESIRED_TURN_RATE = 45
# TURN_RATE_AMPLIFIER = DESIRED_TURN_RATE / ((OFF_LINE_REFLECTION - LINE_REFLECTION) / 2)

# Driving variables
DRIVE_SPEED = 100
DRIVE_WITH_PALLET = 50
TURN_RATE_AMPLIFIER = 1
CRANE_SPEED = 200
STOP_DISTANCE = 350
PALET_DISTANCE = 500
GROUND_LIFT_ANGLE = 50

# Bool for driving with pallet
driving_with_pallet = False

# path color
path_color = "red"
# current location
current_location = "Somewhere"
# clear load pallet
clear_road = True

# Color dictionary with all the rgb values
COLORS = {
    "red": (68,23,40),
    "blue": (7,19,37),
    "yellow line": (39,35,10),
    "brown": (14,9,12),
    "black": (0,0,0),
    "purple": (9,10,32),
    "middle circle": (10,12,8),
    "green": (6,24,14),
    "white": (72,86,100)
}

# All the colors of the lines to follow
TMP_COLORS = COLORS.copy()
for color in ["white", "brown", "black"]:
    del TMP_COLORS[color]
LINE_COLORS = TMP_COLORS.keys()

# Calibrating colors
def calibrate_colors(COLORS):
    # Temporary COLORS dict to change
    temp_colors = COLORS.copy()
    # Loops trough all the colors to update their values
    for key in temp_colors:
        print_on_screen("Select color " + key)
        # Wait untill you press center button on ev3 to update the colors
        while True:
            if Button.CENTER in ev3.buttons.pressed():
                temp_colors[key] = colour_sensor.rgb()
                wait(1000) # Wait between each press so that it wont double press and take two colors
                break
    ev3.screen.clear() # Reset screen
    wait(2000) # Wait two seconds before moving on so that you can move it
    return temp_colors # Returns temp_colors
    
    # print_on_screen, clears screen and prints new text
def print_on_screen(text): 
    ev3.screen.clear()
    ev3.screen.print(str(text))

    # Classify color
def classify_color(rgb_in):
    OFFSET = 8 # Offset for each color value
    match_r = [] 
    match_g = []
    match_b = []
    r_in, g_in, b_in = rgb_in
    # Goes through every color and checks if each of the values are within the offset of the color value
    # If they are whitin the offset they are added to the matches
    for color_key in COLORS.keys():
        r, g, b = COLORS[color_key]
        if r_in < (r + OFFSET) and r_in > (r - OFFSET):
            match_r.append(color_key)
        if g_in < (g + OFFSET) and g_in > (g - OFFSET):
            match_g.append(color_key)
        if b_in < (b + OFFSET) and b_in > (b - OFFSET):
            match_b.append(color_key)
    matches = []
    # Checks if all the color values are within the offset if so adds the color to matches
    for color_key in COLORS.keys():
        if color_key in match_r and color_key in match_g and color_key in match_b:
            matches.append(color_key)
    # If no colors are detected return None
    if len(matches) == 0:
        return [None]
    # print(matches)
    return matches

# Compars arrays returns True if there are matches in the arrays, False if there are None
def compare_arrays(array_1, array_2):
    matches = 0
    for element1 in array_1:
        for element2 in array_2:
            if element1 == element2:
                matches += 1
    if matches != 0:
        return True
    return False

# Searching for the correct path while driving along the cirkle
def select_path():
    global current_location
    print_on_screen("Searching for " + path_color + " path.")
    """
    Antagande:
    Trucken befinner sig på den gula mutt-ringen.
    Resultat:
    Trucken hittar vägen av önskad färg och svänger mot den.
    """
    while path_color not in classify_color(colour_sensor.rgb()):
        # print (classify_color(colour_sensor.rgb())[0])
        if compare_arrays(classify_color(colour_sensor.rgb()), ["red", "blue",]):
            robot.straight(50)
        else:
            follow_color()
    align_right()
    current_location = path_color
    print_on_screen('Found path to ' + current_location +  ' warehouse.')
    
def drive_to_destination():
    global current_location
    print_on_screen('Driving to ' + current_location + ' warehouse.')
    """
    Antagande:
    Trucken har hittat önskad väg och är justerad efter dess riktning.
    Resultat:
    Trucken kör fram till den svarta ytan där vägen möter varuhuset.
    """
    while "black" not in classify_color(colour_sensor.rgb()):
        follow_color()
    robot.drive(0, 0)
    print_on_screen('Arrived at ' + current_location + ' warehouse.')

def return_to_circle():
    global current_location
    print_on_screen('Leaving ' + current_location + ' warehouse and returning to the middle circle.')
    """
    Antagande:
    Trucken står på den svarta ytan i ett lager med nosen innåt i lagret.
    Resultat:
    Trucken svänger ut och kör tillbaka till mitt-cirkeln.
    """
    while "middle circle" not in classify_color(colour_sensor.rgb()):
        if "black" in classify_color(colour_sensor.rgb()):
            robot.drive(0, 45)
            wait(3000)
            robot.drive(0, 0)
        else:
            follow_color()
    align_right()
    print_on_screen('Arrived at the middle circle.')

def align_right():
    robot.turn(-120)
    robot.drive(0, 0)

# def drive_forward(precise = True) -> None:
#     deviation = max(LINE_REFLECTION, colour_sensor.reflection()) - threshold
#     turn_rate = TURN_RATE_AMPLIFIER * deviation
#     drive_speed = 75
#     if driving_with_pallet == True:
#         drive_speed = 40
#     if precise:
#         # speed = drive_speed / (0.8 + abs(deviation) * 0.06)
#         speed = drive_speed * max(0.1, 1 - (abs(turn_rate) / DESIRED_TURN_RATE))
#     else:
#         speed = drive_speed
#     robot.drive(speed, turn_rate)

def deviation_from_rgb(rgb_in, line_color):
    sum_white = sum(COLORS['white'])
    sum_line = sum(line_color)
    threshold = (sum_white + sum_line) / 2
    sum_in = sum(rgb_in)
    deviation = sum_in - threshold
    return deviation

def follow_line(rgb_in, line_color = COLORS['red']) -> None:
    deviation = deviation_from_rgb(rgb_in, line_color)
    turn_rate = TURN_RATE_AMPLIFIER * deviation
    drive_speed = DRIVE_SPEED
    if driving_with_pallet == True:
        drive_speed = DRIVE_WITH_PALLET
    speed = drive_speed / (0.9 + abs(deviation) * 0.05)
    robot.drive(speed, turn_rate)

def follow_color(color_array = LINE_COLORS):
    global clear_road
    if(clear_road):
        drive_speed = 100
    if driving_with_pallet == True:
        drive_speed = -40
    turn_rate = 35
    while compare_arrays(color_array, classify_color(colour_sensor.rgb())):
        turn_rate = 0
        drive_speed = 0
        robot.turn(-20)
        if compare_arrays(color_array, classify_color(colour_sensor.rgb())):
            robot.turn(45)
            robot.straight(-70)
    robot.drive(drive_speed, turn_rate)
    #else:
    #    robot.drive(0,0)

def find_pallet(is_pallet_on_ground: bool) -> None:
    print_on_screen('Searching for a pallet.')
    """
    Antagande:
    Vi står i varuhuset
    Resultat:
    Vi är redo att köra pickup pallet, med eller utan höjd
    """
    while "yellow line" not in classify_color(colour_sensor.rgb()):
        robot.drive(40,-20)
    while ultrasonic_sensor.distance()> PALET_DISTANCE:
        follow_color(["yellow line"])
    print_on_screen("Found pallet")
    if (is_pallet_on_ground):
        pick_up_pallet_on_ground()
    elif(is_pallet_on_ground == False ):#elif 
        #pick_up
        pick_up_pallet_in_air()

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
    stop_after_time = 20
    drive_forward_time = time.perf_counter()
    robot.reset()
    
    while(not is_pallet_on_properly and (time.perf_counter() -drive_forward_time) <stop_after_time):
        is_pallet_on_properly = touch_sensor.pressed()
        follow_color(["yellow line"])
    drive_forward_stop_time = time.perf_counter()
    robot.drive(0, 0)
    if not is_pallet_on_properly:
        print_on_screen("Picking up failed.")
    else:
        print_on_screen("picking up")
        Crane_motor.reset_angle(0)
        Crane_motor.run_angle(CRANE_SPEED, GROUND_LIFT_ANGLE)
        driving_with_pallet = True
    time_to_back_out = drive_forward_stop_time -  drive_forward_time
    distance_to_back_out = (time_to_back_out * drive_speed_crawl) /1000 #(ms *mm/s)/m
    distance_to_back_out = robot.distance()
    robot.straight(-distance_to_back_out)    
    #Sväng om?
def reset_crane():
    Crane_motor.run_until_stalled(CRANE_SPEED)
    Crane_motor.run_until_stalled(-CRANE_SPEED)

# Main thread for driving etc
def main():
    while(True):
        follow_line(colour_sensor.rgb())
        
def get_color():
    while (True):
        global path_color
        color = input("Choose color... ")
        if str(color).lower() in COLORS.keys():
            path_color = color.lower()
            print(color)
            
        else:
            print("No color matching input")

def collision_check():
    while True:
        global clear_road
        if ultrasonic_sensor.distance() < STOP_DISTANCE:
            clear_road = False
        else:
            clear_road = True
# COLORS = calibrate_colors(COLORS)

_thread.start_new_thread(collision_check,(),)
_thread.start_new_thread(main,(),)
_thread.start_new_thread(get_color,(),)

while True:
    pass
