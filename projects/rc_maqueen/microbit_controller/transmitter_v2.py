DEADZONE = 200
RADIO_GROUP = 90

def setup():
    radio.set_group(RADIO_GROUP)
    basic.show_icon(IconNames.HEART)

def direction_arrow():
    straight = -input.acceleration(Dimension.Y)
    turn = input.acceleration(Dimension.X)
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
    straight = -input.acceleration(Dimension.Y)
    turn = input.acceleration(Dimension.X)
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

basic.forever(loop)
