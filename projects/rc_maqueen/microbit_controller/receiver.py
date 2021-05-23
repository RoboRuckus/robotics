# The following extensions are required:
# * MaqueenPlus
# This program is block-code compatible.
def on_received_number(receivedNumber):
    global received
    received = receivedNumber
    if receivedNumber == 0:
        DFRobotMaqueenPlus.motot_run(Motors.M1, Dir.CW, 128)
        basic.show_leds("""
            . . # . .
            . . . # .
            # # # # #
            . . . # .
            . . # . .
            """)
    else:
        if receivedNumber == 1:
            DFRobotMaqueenPlus.motot_run(Motors.M2, Dir.CW, 128)
            basic.show_leds("""
                . . # . .
                . # . . .
                # # # # #
                . # . . .
                . . # . .
                """)
        else:
            if receivedNumber == 2:
                DFRobotMaqueenPlus.motot_run(Motors.ALL, Dir.CW, 128)
                basic.show_leds("""
                    . . # . .
                    . # # # .
                    # . # . #
                    . . # . .
                    . . # . .
                    """)
            else:
                if receivedNumber == 4:
                    DFRobotMaqueenPlus.motot_run(Motors.ALL, Dir.CCW, 128)
                    basic.show_leds("""
                        . . # . .
                        . . # . .
                        # . # . #
                        . # # # .
                        . . # . .
                        """)
                else:
                    DFRobotMaqueenPlus.motot_run(Motors.ALL, Dir.CW, 0)
                    basic.show_icon(IconNames.NO)
radio.on_received_number(on_received_number)

received = 0
radio.set_group(90)
