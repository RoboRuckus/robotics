# The following extensions are required:
# * MaqueenPlus
# This program is block-code compatible.
radio.set_group(90)

def on_forever():
    if input.acceleration(Dimension.X) > 700:
        radio.send_number(0)
        basic.show_leds("""
            . . # . .
            . . . # .
            # # # # #
            . . . # .
            . . # . .
            """)
    else:
        if input.acceleration(Dimension.X) < -700:
            radio.send_number(1)
            basic.show_leds("""
                . . # . .
                . # . . .
                # # # # #
                . # . . .
                . . # . .
                """)
        else:
            if input.acceleration(Dimension.Y) < -700:
                radio.send_number(2)
                basic.show_leds("""
                    . . # . .
                    . # # # .
                    # . # . #
                    . . # . .
                    . . # . .
                    """)
            else:
                if input.acceleration(Dimension.Y) > 700:
                    radio.send_number(4)
                    basic.show_leds("""
                        . . # . .
                        . . # . .
                        # . # . #
                        . # # # .
                        . . # . .
                        """)
                else:
                    radio.send_number(3)
                    basic.show_icon(IconNames.NO)
basic.forever(on_forever)
