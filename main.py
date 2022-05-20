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
import json

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

# Driving variables
DRIVE_SPEED = 200
DRIVE_WITH_PALLET = 100
TURN_RATE_AMPLIFIER = 1.3 # 1 för robot 8, 1.8 för robot 4
CRANE_SPEED = 200
STOP_DISTANCE = 350
PALET_DISTANCE = 500
GROUND_LIFT_ANGLE = 150

# Global variables
clear_road = True
driving_with_pallet = False
selected_path_color = "red"
current_location = "middle circle"
emergency_mode = False

# Standard rgb values for colors
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

# Different locations
LOCATIONS = {
    "red": Color.RED,
    "blue": Color.BLUE,
    "purple": Color.BLUE,
    "middle circle": Color.YELLOW,
    "green": Color.GREEN,
    "red warehouse": Color.RED,
    "blue warehouse": Color.BLUE
}

TMP_COLORS = COLORS.copy()
for color in ["white", "brown", "black"]:
    del TMP_COLORS[color]
LINE_COLORS = TMP_COLORS.keys()

def calibrate_colors(COLORS):
    """
    Creates a dictionary with rgb values for each colors.
    The function lets the user copy the rgb values for colors
    by holding the color sensor over the requested color wich
    shows up on the ev3 hub screen
    """
    temp_colors = COLORS.copy()
    for key in temp_colors:
        print_on_screen("Select color " + key)
        while True:
            if Button.CENTER in ev3.buttons.pressed():
                temp_colors[key] = colour_sensor.rgb()
                wait(1000)
                break
    ev3.screen.clear()
    wait(2000)
    return temp_colors
    
def open_file_colors(COLORS):
    """
    Opens or creates a new file that saves colors rgb values.
    """
    with open('RGB.txt', 'w') as convert_file:
     convert_file.write(json.dumps(COLORS))

def print_on_screen(text):
    """
    Clears the screen on the ev3 hub and prints string input instead.
    """
    ev3.screen.clear()
    ev3.screen.print(str(text))

def change_color(color_key):
    """
    Changes the color of the light on the ev3 hub.
    """
    ev3.light.on(LOCATIONS[color_key])

def classify_color(rgb_in, offset = None):
    """
    Uses the rgb values from the color sensor to decide what color it
    detects based on predetermined values of each colors rgb values
    takes the rgb values aswell as an allowed offset as arguments
    """
    OFFSET = 4
    if offset is None:
        offset = OFFSET
    match_r = [] 
    match_g = []
    match_b = []
    r_in, g_in, b_in = rgb_in
    for color_key in COLORS.keys():
        r, g, b = COLORS[color_key]
        if r_in < (r + offset) and r_in > (r - offset):
            match_r.append(color_key)
        if g_in < (g + offset) and g_in > (g - offset):
            match_g.append(color_key)
        if b_in < (b + offset) and b_in > (b - offset):
            match_b.append(color_key)
    matches = []
    for color_key in COLORS.keys():
        if color_key in match_r and color_key in match_g and color_key in match_b:
            matches.append(color_key)
    if len(matches) == 0:
        return [None]
    return matches

def compare_arrays(array_1, array_2):
    """
    Compares to arrays and return True if the elements in
    array 1 exists in array 2
    """
    matches = 0
    for element1 in array_1:
        for element2 in array_2:
            if element1 == element2:
                matches += 1
    if matches != 0:
        return True
    return False

def select_path():
    """
    Drives around the middle circle util it finds the path that
    corresponds with the global variable selected_path_color and skips the paths
    that does not.
    """
    global current_location
    global selected_path_color
    global driving_with_pallet
    ev3.light.on(Color.YELLOW)
    print_on_screen("Searching for " + selected_path_color + " path.")

    color = colour_sensor.rgb()
    while selected_path_color not in classify_color(color):
        if compare_arrays(classify_color(color), ["red", "blue" , "purple" , "green"]):
            robot.straight(70)
        else:
            follow_line(color)
        color = colour_sensor.rgb()
    print("I found the path! Are you proud? :)")
    if driving_with_pallet:
        align_right()
    current_location = selected_path_color
    change_color(current_location)
    
def drive_to_destination():
    """
    The robot drives from the middle circle to the warehouse when
    the correct path is found untill it sees black which is the 
    entry to each warehouse.
    """
    global current_location
    print_on_screen('Driving to ' + current_location + ' warehouse.')
    color = colour_sensor.rgb()
    while colour_sensor.color() != Color.BLACK:
        follow_line(color)
        color = colour_sensor.rgb()
    robot.drive(0, 0)
    change_color(current_location)

def return_to_circle():
    """
    The truck drives from the warehouse back to the circle by driving untill
    it detects the color of the middlecircle.
    """
    global current_location
    print_on_screen('Leaving ' + current_location + ' warehouse and returning to the middle circle.')
    robot.turn(300)
    ev3.speaker.say("Leaving " +  current_location)
    color = colour_sensor.rgb()
    while ("middle circle" not in classify_color(color,20)):
        follow_line(color)
        color = colour_sensor.rgb()
    align_right()
    current_location = 'middle circle'
    change_color(current_location)
    print_on_screen('Arrived at the middle circle.')
    
def return_to_area(location_override = None):
    """
    Depending on what area the robot is leaving this function changes
    what path color the robot should look for and drives it back to the middle circle.
    """
    global selected_path_color
    global current_location
    if location_override != None:
        current_location = location_override
    if current_location == "middle circle":
        selected_path_color = "green"
    elif current_location == "red warehouse":
        selected_path_color = "green"
        return_to_circle()
    elif current_location == "blue warehouse":
        selected_path_color = "green"
        return_to_circle()
    elif current_location == "pickup and delivery":
        selected_path_color = "red"
        return_to_circle()

def align_right():
    """
    Tells the robot to turn different amounts depending on if the robot
    carries a pallet or not.
    """
    global driving_with_pallet
    if driving_with_pallet:
        robot.straight(-100)
        robot.turn(-270)
        robot.drive(0, 0)
    elif driving_with_pallet == False:
        robot.turn(-170)
        robot.drive(0,0)

def deviation_from_rgb(rgb_in, line_color):
    """
    Calculates the deviation of the current rgb values from the color sensor
    to the average between white and the line the robot is supposed to follow.
    """
    sum_white = sum(COLORS['white'])
    sum_line = sum(line_color)
    threshold = (sum_white + sum_line) / 2
    sum_in = sum(rgb_in)
    deviation = sum_in - threshold
    return deviation

def follow_line(rgb_in, line_color = COLORS['red']) -> None:
    """
    Follows the selected line, takes the rgb values of the color sensor and
    what color to follow as arguments. The robot follows the line based of the
    deviation from the function "deviation_from_rgb()".
    """
    global clear_road
    global driving_with_pallet
    deviation_turn_offset = 1
    if emergency_mode:
        pass
    else:
        if clear_road:
            deviation = deviation_from_rgb(rgb_in, line_color)
            sum_white = sum(COLORS['white'])
            sum_line = sum(line_color)
            threshold = (sum_white - sum_line) / 2
            turn_rate = TURN_RATE_AMPLIFIER * deviation
            drive_speed = DRIVE_SPEED
            if driving_with_pallet == True:
                drive_speed = DRIVE_WITH_PALLET
            speed = drive_speed / (0.9 + abs(deviation) * 0.01)
            if (abs(deviation) + deviation_turn_offset >= threshold) and (deviation < 0):
                robot.drive(0,0)
                turn_rate = 0
                drive_speed = 0
                robot.turn(-25)
                deviation = deviation_from_rgb(colour_sensor.rgb(), line_color)
                if (abs(deviation) + deviation_turn_offset >= threshold) and (deviation < 0) and (colour_sensor.color() != Color.BLACK):
                    robot.turn(-45)
                    robot.straight(-60)
            else:
                robot.drive(speed, turn_rate)
        else:
            robot.drive(0,0)

def follow_color(color_array = LINE_COLORS):
    """
    This function allows the robot to follow a line by checking if it sees the color of the
    line, if it does it will turn right and then drive forward while going a bit left untill
    it sees the color again. 
    """
    drive_speed = 100
    if driving_with_pallet == True:
        drive_speed = 40
    turn_rate = 35
    while compare_arrays(color_array, classify_color(colour_sensor.rgb())):
        robot.drive(0,0)
        robot.turn(-20)
        if compare_arrays(color_array, classify_color(colour_sensor.rgb())):
            robot.turn(-45)
            robot.straight(-70)
    robot.drive(drive_speed, turn_rate)

def find_pallet(is_pallet_on_ground: bool) -> None:
    """
    When entering a warehouse the robot drives untill it finds a yellow line,
    left or right depending on what warehouse it is in. Then it checks if 
    there is a pallet infront of it. If there is it runs the pickup pallet 
    function. If there isn't it crosses the yellow line and drives to the next
    line and checks there.
    """
    print_on_screen('Searching for a pallet.')
    global current_location
    global driving_with_pallet
    pallet_position = 1
    if current_location == 'red':
        current_location = "red warehouse"
        if ultrasonic_sensor.distance() < PALET_DISTANCE + 150:
            pallet_position = 1
            while "yellow line" not in classify_color(colour_sensor.rgb()):
                robot.drive(40,20)
            robot.drive(0,0)
            if is_pallet_on_ground:
                pick_up_pallet_on_ground(pallet_position)
            else:
                pick_up_pallet_in_air(pallet_position)

        else:
            pallet_position = 2
            while "yellow line" not in classify_color(colour_sensor.rgb()):
                robot.drive(40,20)
            robot.drive(0,0)
            robot.straight(60)
            while "yellow line" not in classify_color(colour_sensor.rgb()):
                robot.drive(40,0)
            if is_pallet_on_ground:
                pick_up_pallet_on_ground(pallet_position)
            else:
                pick_up_pallet_in_air(pallet_position)

    elif current_location == 'blue':
        current_location = "blue warehouse"
        if ultrasonic_sensor.distance() < PALET_DISTANCE + 150:
            pallet_position = 1
            while "yellow line" not in classify_color(colour_sensor.rgb()):
                robot.drive(40, -20)
            robot.drive(0,0)
            robot.turn(-15)
            robot.straight(60)
            if is_pallet_on_ground:
                pick_up_pallet_on_ground(pallet_position)
            else:
                pick_up_pallet_in_air(pallet_position)
            robot.turn(240)
            while 'blue' not in classify_color(colour_sensor.rgb()):
                robot.drive(-100, 0)

        else:
            pallet_position = 2
            while "yellow line" not in classify_color(colour_sensor.rgb()):
                robot.drive(40,-20)
            robot.drive(0,0)
            robot.straight(60)
            while "yellow line" not in classify_color(colour_sensor.rgb()):
                robot.drive(40,0)
            robot.drive(0,0)
            if is_pallet_on_ground:
                pick_up_pallet_on_ground(pallet_position)
            else:
                pick_up_pallet_in_air(pallet_position)
            robot.turn(240)
            while 'blue' not in classify_color(colour_sensor.rgb()):
                robot.drive(100, 0)
            robot.straight(70)
        

    elif current_location == "green":
        current_location = "pickup and delivery"
        wait(5000)
        driving_with_pallet = False

def pick_up_pallet_in_air(pallet_position) -> None:
    """
    Runs if the pallet is elevated and sets the starting position of the crane
    to an elevated position before running the pickup pallet function.
    """
    Crane_motor.run_angle(CRANE_SPEED, 200)
    pick_up_pallet_on_ground(pallet_position)
    Crane_motor.run_angle(-CRANE_SPEED, 200)

def pick_up_pallet_on_ground(pallet_position) -> None:
    """
    Drive forward and pickup the pallet then reverse back to the starting position
    """
    print_on_screen('Picking up the found pallet.')
    global driving_with_pallet
    is_pallet_on_properly = False
    drive_speed_crawl = 60
    stop_after_time = 30
    drive_forward_time = time.perf_counter()
    robot.reset()
    robot.drive(0,0)
    
    reset_crane()

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
        Crane_motor.run_target(CRANE_SPEED, GROUND_LIFT_ANGLE)
        driving_with_pallet = True
    time_to_back_out = drive_forward_stop_time -  drive_forward_time
    distance_to_back_out = (time_to_back_out * drive_speed_crawl) /1000
    distance_to_back_out = robot.distance()
    if pallet_position == 1:
        robot.straight(-distance_to_back_out)
    elif pallet_position == 2:
        robot.straight(-distance_to_back_out * 2)

def reset_crane():
    """
    Lifts the crane then lowers it down to ground level.
    """
    Crane_motor.run_until_stalled(CRANE_SPEED)
    Crane_motor.run_until_stalled(-CRANE_SPEED)

def main():
    """
    The main function that runs the whole program
    """
    while(True):
        select_path()
        drive_to_destination()
        find_pallet(True)
        return_to_area()

def main2():
    global driving_with_pallet
    driving_with_pallet = True
    return_to_circle()
    select_path()

def get_color():
    """
    Lets the user enter the color of the pallets the robot shall collect
    """
    while (True):
        global selected_path_color
        color = input("Choose color... ")
        if str(color).lower() in COLORS.keys():
            selected_path_color = color.lower()
            print(color)
            
        else:
            print("No color matching input")

def collision_check():
    """
    Checks if there is something infront of the robot
    """
    global clear_road
    while True:
        if (ultrasonic_sensor.distance() < STOP_DISTANCE) and (driving_with_pallet == False):
            clear_road = False
        else:
            clear_road = True

def check_emergency():
    """
    If the pallet is dropped the robot enters emergency mode and drives to the side off the road
    """
    global driving_with_pallet
    global emergency_mode
    while True:
        if (driving_with_pallet == True) and (touch_sensor.pressed() == False) and (emergency_mode == False):
            emergency_mode = True
            robot.turn(120)
            robot.straight(-400)
            print_on_screen("HELP THERE IS A PALLET IN MY WAY")
   
        elif (driving_with_pallet == True) and (touch_sensor.pressed() == True) and (emergency_mode == True):
            robot.straight(360)
            robot.turn(-120)
            print_on_screen("LETS GOOO")
            emergency_mode = False

# Adding color values to file for saving while also calibrating
open_file_colors(calibrate_colors(COLORS))

with open('RGB.txt') as f:
    data = f.read()

# reconstructing the data as a dictionary
COLORS = json.loads(data)
print(COLORS)

_thread.start_new_thread(collision_check,(),)
_thread.start_new_thread(main,(),)
_thread.start_new_thread(get_color,(),)
_thread.start_new_thread(check_emergency,(),)

while True:
    pass