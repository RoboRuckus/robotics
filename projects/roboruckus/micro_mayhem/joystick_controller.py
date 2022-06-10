# Which radio group to transmit to, will need to vary this between bots
RADIO_GROUP = 90

# We can only transmit numbers via send_value, create ENUM
LEFT = 0
RIGHT = 1

FORWARD = 0
BACKWARD = 1

# Joystick Related
JOYSTICK_DEADZONE = 20
MANUAL_CONTROL = False

def setup():
  basic.show_icon(IconNames.HEART)
  radio.set_group(RADIO_GROUP)
  radio.on_received_value(receive_message)
  input.on_button_pressed(Button.B, toggle_joystick)
  joystickbit.init_joystick_bit()
  joystickbit.on_button_event(joystickbit.JoystickBitPin.P12, joystickbit.ButtonType.DOWN, turn_left_90)
  joystickbit.on_button_event(joystickbit.JoystickBitPin.P13, joystickbit.ButtonType.DOWN, move_forward)
  joystickbit.on_button_event(joystickbit.JoystickBitPin.P14, joystickbit.ButtonType.DOWN, move_backward)
  joystickbit.on_button_event(joystickbit.JoystickBitPin.P15, joystickbit.ButtonType.DOWN, turn_right_90)
  basic.clear_screen()

# def calibrate():

def loop():
  if MANUAL_CONTROL == True:
    direction_arrow()
    send_direction()

def joystick_x():
    # return input.acceleration(Dimension.X)
    return -(joystickbit.get_rocker_value(joystickbit.rockerType.X) - 500)

def joystick_y():
    # return input.acceleration(Dimension.Y)
    return -(joystickbit.get_rocker_value(joystickbit.rockerType.Y) - 500)

def send_message(key, value):
  radio.send_value(key, value)

def receive_message(key, value):
  if key == 'turning':
    show_turning(value)
  elif key == 'moving':
    show_moving(value)
  elif key == 'done':
    basic.clear_screen()

def show_turning(value):
  if value == LEFT:
    basic.show_leds("""
                    . . # . .
                    . # . . .
                    # # # # #
                    . # . . .
                    . . # . .
                    """)
  elif value == RIGHT:
    basic.show_leds("""
                    . . # . .
                    . . . # .
                    # # # # #
                    . . . # .
                    . . # . .
                    """)

def show_moving(value):
  if value == FORWARD:
    basic.show_leds("""
                    . . # . .
                    . # # # .
                    # . # . #
                    . . # . .
                    . . # . .
                    """)
  elif value == BACKWARD:
    basic.show_leds("""
                    . . # . .
                    . . # . .
                    # . # . #
                    . # # # .
                    . . # . .
                    """)

def direction_arrow():
    straight = -joystick_y()
    turn = joystick_x()
    if straight > JOYSTICK_DEADZONE:
        if turn > JOYSTICK_DEADZONE:
            basic.show_leds("""
                            . # # # #
                            . . . # #
                            . . # . #
                            . # . . #
                            # . . . .
                            """)
        elif turn < -JOYSTICK_DEADZONE:
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
    elif straight < -JOYSTICK_DEADZONE:
        if turn > JOYSTICK_DEADZONE:
            basic.show_leds("""
                            # . . . .
                            . # . . #
                            . . # . #
                            . . . # #
                            . # # # #
                            """)
        elif turn < -JOYSTICK_DEADZONE:
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
        if turn > JOYSTICK_DEADZONE:
            basic.show_leds("""
                            . . # . .
                            . . . # .
                            # # # # #
                            . . . # .
                            . . # . .
                            """)
        elif turn < -JOYSTICK_DEADZONE:
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

def send_direction():
    straight = -joystick_y()
    turn = joystick_x()
    if abs(straight) > JOYSTICK_DEADZONE:
        send_message('straight', straight)
    else:
        send_message('straight', 0)
    if abs(turn) > JOYSTICK_DEADZONE:
        send_message('turn', turn)
    else:
        send_message('turn', 0)

def move_forward():
  basic.show_icon(IconNames.TRIANGLE)
  send_message('move', FORWARD)
  basic.clear_screen()

def move_backward():
  basic.show_icon(IconNames.NO)
  send_message('move', BACKWARD)
  basic.clear_screen()

def turn_right_90():
  basic.show_leds("""
                  . # # # .
                  # . . . #
                  # . . . #
                  # . . . #
                  . # # # .
                  """)
  send_message('turn', RIGHT)
  basic.clear_screen()

def turn_left_90():
  basic.show_icon(IconNames.SQUARE)
  send_message('turn', LEFT)
  basic.clear_screen()

def toggle_joystick():
  global MANUAL_CONTROL
  MANUAL_CONTROL = not MANUAL_CONTROL
  basic.clear_screen()

setup()
basic.forever(loop)
