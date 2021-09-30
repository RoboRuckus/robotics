# The following extensions are required:
# * MaqueenPlus
# This program is not block-code compatible.
DEADZONE = 20
RADIO_GROUP = 90

def x_input():
    # return input.acceleration(Dimension.X)
    return -(joystickbit.get_rocker_value(joystickbit.rockerType.X) - 500)

def y_input():
    # return input.acceleration(Dimension.Y)
    return -(joystickbit.get_rocker_value(joystickbit.rockerType.Y) - 500)

def setup():
    radio.set_group(RADIO_GROUP)
    joystickbit.init_joystick_bit()
    basic.show_icon(IconNames.HEART)

def direction_arrow():
    straight = -y_input()
    turn = x_input()
    if straight > DEADZONE:
        if turn > DEADZONE:
            basic.show_leds("""
                            . # # # #
                            . . . # #
                            . . # . #
                            . # . . #
                            # . . . .
                            """)
        elif turn < -DEADZONE:
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
    elif straight < -DEADZONE:
        if turn > DEADZONE:
            basic.show_leds("""
                            # . . . .
                            . # . . #
                            . . # . #
                            . . . # #
                            . # # # #
                            """)
        elif turn < -DEADZONE:
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
        if turn > DEADZONE:
            basic.show_leds("""
                            . . # . .
                            . . . # .
                            # # # # #
                            . . . # .
                            . . # . .
                            """)
        elif turn < -DEADZONE:
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
    straight = -y_input()
    turn = x_input()
    if abs(straight) > DEADZONE:
        radio.send_value('straight', straight)
    else:
        radio.send_value('straight', 0)
    if abs(turn) > DEADZONE:
        radio.send_value('turn', turn)
    else:
        radio.send_value('turn', 0)

def loop():
    direction_arrow()
    send_direction()

setup()
basic.forever(loop)
