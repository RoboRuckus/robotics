# ---------------
# Hardware Values
# ---------------

RADIO_GROUP = 90
RADIO_DEADZONE = 200
RADIO_MAX = 1024

LEFT_MOTOR = Motors.M1
RIGHT_MOTOR = Motors.M2

FORWARD = Dir.CW
REVERSE = Dir.CCW

MAX_SPEED = 128

# -----------
# Code Begins
# -----------

straight_channel = 0
turn_channel = 0
left_motor_speed = 0
right_motor_speed = 0

def constrain(val, min_val, max_val):
    return min(max_val, max(min_val, val))

def translate(value, left_min, left_max, right_min, right_max):
    left_span = left_max - left_min
    right_span = right_max - right_min
    # Convert the left range into a 0-1 range float
    value_scaled = (value - left_min) / left_span
    # Convert the 0-1 range into a value in the right range
    return right_min + (value_scaled * right_span)

def on_received_value(name, value):
    global straight_channel
    global turn_channel
    if name == 'straight':
        straight_channel = value
    elif name == 'turn':
        turn_channel = value

def radio_to_speed(radio_value):
    speed = translate(radio_value, -RADIO_MAX, RADIO_MAX, -MAX_SPEED, MAX_SPEED)
    speed = constrain(speed, -MAX_SPEED, MAX_SPEED)
    return speed

# Lazy implementation of mixing
def calculate_speeds_from_radio():
    global left_motor_speed
    global right_motor_speed
    # Reset to 0
    left_motor_speed = 0
    right_motor_speed = 0
    # Forward/Backward
    if abs(straight_channel) > RADIO_DEADZONE:
        left_motor_speed = radio_to_speed(straight_channel)
        right_motor_speed = radio_to_speed(straight_channel)
    # Left/Right
    if abs(turn_channel) > RADIO_DEADZONE:
        left_motor_speed += radio_to_speed(turn_channel/2)
        right_motor_speed -= radio_to_speed(turn_channel/2)
    # Constrain motors to max speed when mixing
    left_motor_speed = constrain(left_motor_speed, -MAX_SPEED, MAX_SPEED)
    right_motor_speed = constrain(right_motor_speed, -MAX_SPEED, MAX_SPEED)

def set_motor_speeds():
    if left_motor_speed > 0:
        DFRobotMaqueenPlus.motot_run(LEFT_MOTOR, FORWARD, left_motor_speed)
    elif left_motor_speed < 0:
        DFRobotMaqueenPlus.motot_run(LEFT_MOTOR, REVERSE, abs(left_motor_speed))
    else:
        DFRobotMaqueenPlus.motot_stop(LEFT_MOTOR)

    if right_motor_speed > 0:
        DFRobotMaqueenPlus.motot_run(RIGHT_MOTOR, FORWARD, right_motor_speed)
    elif right_motor_speed < 0:
        DFRobotMaqueenPlus.motot_run(RIGHT_MOTOR, REVERSE, abs(right_motor_speed))
    else:
        DFRobotMaqueenPlus.motot_stop(RIGHT_MOTOR)

def direction_arrow():
    if straight_channel > RADIO_DEADZONE:
        if turn_channel > RADIO_DEADZONE:
            basic.show_leds("""
                            . # # # #
                            . . . # #
                            . . # . #
                            . # . . #
                            # . . . .
                            """)
        elif turn_channel < -RADIO_DEADZONE:
            basic.show_leds("""
                            # # # # .
                            # # . . .
                            # . # . .
                            # . . # .
                            . . . . #
                            """)
        else:
            basic.show_leds("""
                            . . # . .
                            . # # # .
                            # . # . #
                            . . # . .
                            . . # . .
                            """)
    elif straight_channel < -RADIO_DEADZONE:
        if turn_channel > RADIO_DEADZONE:
            basic.show_leds("""
                            # . . . .
                            . # . . #
                            . . # . #
                            . . . # #
                            . # # # #
                            """)
        elif turn_channel < -RADIO_DEADZONE:
            basic.show_leds("""
                            . . . . #
                            # . . # .
                            # . # . .
                            # # . . .
                            # # # # .
                            """)
        else:
            basic.show_leds("""
                            . . # . .
                            . . # . .
                            # . # . #
                            . # # # .
                            . . # . .
                            """)
    else:
        if turn_channel > RADIO_DEADZONE:
            basic.show_leds("""
                            . . # . .
                            . . . # .
                            # # # # #
                            . . . # .
                            . . # . .
                            """)
        elif turn_channel < -RADIO_DEADZONE:
            basic.show_leds("""
                            . . # . .
                            . # . . .
                            # # # # #
                            . # . . .
                            . . # . .
                            """)
        else:
            basic.show_leds("""
                            . # # # .
                            # . . . #
                            # . . . #
                            # . . . #
                            . # # # .
                            """)

def setup():
    basic.show_icon(IconNames.HEART)
    radio.on_received_value(on_received_value)
    radio.set_group(RADIO_GROUP)
    DFRobotMaqueenPlus.i2c_init()

def loop():
    calculate_speeds_from_radio()
    set_motor_speeds()
    direction_arrow()
    # basic.pause(25) # Keep the refresh rate sane

setup()
basic.forever(loop)
