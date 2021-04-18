# -------
# IO Pins
# -------

PPM_PIN = DigitalPin.P8
PPM_PIN_EVT_ID = EventBusSource.MICROBIT_ID_IO_P8

# ---------------
# Hardware Values
# ---------------

RX_CHANNEL_COUNT = 8
# Amount of deadzone to apply to the joystick
RX_DEADZONE = 7

LEFT_MOTOR = Motors.M1
RIGHT_MOTOR = Motors.M2

FORWARD = Dir.CW
REVERSE = Dir.CCW

MAX_SPEED = 255

# --------------
# Radio Settings
# --------------

# Each PPM frame can be of variable length, depending on the values of each
# channel. The start of a frame is indicated with a high state that lasts over
# 2ms (2000μs). The delay between channel pulses is typically 300μs, and each
# channel pulse is normally between 700-1700μs, to give a channel range of
# 1000-2000.

SIGNAL_METHOD = EventBusValue.MICROBIT_PIN_EVT_FALL
START_FRAME_LENGTH = 2200

# -----------
# Code Begins
# -----------

rx_channel_data = [2000,0,0,0,0,0,0,0,0]

current_channel = 0
previous_time = input.running_time_micros()

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

def ppm_to_speed(ppm_value):
    speed = translate(ppm_value, 1000, 2000, -MAX_SPEED, MAX_SPEED)
    speed = constrain(speed, -MAX_SPEED, MAX_SPEED)
    return speed

def ppm_interrupt():
    global current_channel
    global previous_time
    current_time = input.running_time_micros()
    delta_time = current_time - previous_time
    previous_time = current_time

    if (delta_time > START_FRAME_LENGTH) or (current_channel > RX_CHANNEL_COUNT):
        current_channel = 0
    rx_channel_data[current_channel] = delta_time
    current_channel += 1

def write_ppm_to_serial():
    serial.write_numbers(rx_channel_data)

# Lazy implementation of mixing
def calculate_speeds_from_ppm():
    global left_motor_speed
    global right_motor_speed
    # Reset to 0
    left_motor_speed = 0
    right_motor_speed = 0
    # Name channels
    straight_channel = rx_channel_data[2]
    turn_channel = rx_channel_data[1]
    # Forward/Backward
    if abs(straight_channel - 1500) > RX_DEADZONE:
        left_motor_speed = ppm_to_speed(straight_channel)
        right_motor_speed = ppm_to_speed(straight_channel)
    # Left/Right
    if abs(turn_channel - 1500) > RX_DEADZONE:
        left_motor_speed += ppm_to_speed(turn_channel)
        right_motor_speed -= ppm_to_speed(turn_channel)
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

def setup():
    basic.show_icon(IconNames.HEART)
    pins.set_events(PPM_PIN, PinEventType.EDGE)
    pins.set_pull(PPM_PIN, PinPullMode.PULL_UP)
    control.on_event(PPM_PIN_EVT_ID, SIGNAL_METHOD, ppm_interrupt)
    DFRobotMaqueenPlus.i2c_init()

def loop():
    # write_ppm_to_serial()
    calculate_speeds_from_ppm()
    set_motor_speeds()
    basic.pause(25) # Keep the refresh rate sane

setup()
basic.forever(loop)
