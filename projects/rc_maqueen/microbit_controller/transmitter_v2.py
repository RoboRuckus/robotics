DEADZONE = 100

def setup():
    radio.set_group(90)

def show_leds():
    if input.acceleration(Dimension.X) > DEADZONE:
        basic.show_leds("""
            . . # . .
            . . . # .
            # # # # #
            . . . # .
            . . # . .
            """)
    else:
        if input.acceleration(Dimension.X) < -DEADZONE:
            basic.show_leds("""
                . . # . .
                . # . . .
                # # # # #
                . # . . .
                . . # . .
                """)
        else:
            if input.acceleration(Dimension.Y) < -DEADZONE:
                basic.show_leds("""
                    . . # . .
                    . # # # .
                    # . # . #
                    . . # . .
                    . . # . .
                    """)
            else:
                if input.acceleration(Dimension.Y) > DEADZONE:
                    basic.show_leds("""
                        . . # . .
                        . . # . .
                        # . # . #
                        . # # # .
                        . . # . .
                        """)
                else:
                    basic.show_icon(IconNames.NO)

def send_direction():
    radio.send_value('straight', input.acceleration(Dimension.X))
    radio.send_value('turn', input.acceleration(Dimension.Y))

def loop():
    show_leds()
    send_direction()

basic.forever(loop)
