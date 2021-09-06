#uPython module: MIT Lesser General Public License Copyright (c) 2021 Technology Alliance Group NW (https://tagnw.org)
#Contributors: ShipShupe

from microbit import *
import radio
from math import atan2, cos, sin, sqrt, pi

DEADZONE = 10
SPEED = 60
TURN_DAMPENING = 1.5
RADIO_GROUP = 1

def map_range(x, in_min, in_max, out_min, out_max):
    return max(min(out_max, (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min), out_min)

def clamp(x, xmin, xmax):
    return max(xmin, min(x, xmax))


#works with Elecfreaks Joystick:Bit, can be adapted for other layouts
class Joystickbit:

    RadioGroup = RADIO_GROUP
    AxisX = pin1
    AxisY = pin2
    Left = [pin12, 0]
    Up = [pin13, 0]
    Right = [pin15, 0]
    Down = [pin14, 0]
    AB = (button_a, button_b)
    ButtonMessages = ((Left, "L"), (Right, "R"), (Down, "B"), (Up, "F"))

    def __init__(self):
        for button in (self.Left, self.Right, self.Up, self.Down):
            button[0].set_pull(button[0].PULL_UP)
        radio.config(group=RADIO_GROUP)
        radio.on()

    def forever(self):
        while True:
            sleep(100)

            #Disable if worried about gamification and chaos. Otherwise, enjoy!
            if button_a.was_pressed():
                self.setRadio(-1)
            elif button_b.was_pressed():
                self.setRadio(1)

            else:
                for button, message in self.ButtonMessages:
                    if J.send_if_pressed(button,message):
                        continue
                J.send_joystick()

    def setRadio(self, increment):
        self.RadioGroup = clamp(self.RadioGroup + increment, 1, 9)
        radio.off()
        radio.config(group=self.RadioGroup)
        radio.on()
        display.show(self.RadioGroup)
        sleep(500)

    def was_pressed(self, button):
        if button in self.AB:
            return button.was_pressed()
        val = button[0].read_digital()
        if val == button[1]:
           return False
        elif val == 0:
            button[1] = val
            return True
        else:
            button[1] = val
            return False

    def send_if_pressed(self, button, message):
        if self.was_pressed(button):
            radio.send(message)
            display.show(message[0])
        return True

    #Joystick middle is ~505, range 0-1010
    #Out should be ~ -SPEED -> SPEED
    def send_joystick(self):
        x = self.AxisX.read_analog() - 505
        y = self.AxisY.read_analog() - 505
        theta = atan2(x, y) + pi/2
        magnitude = clamp(sqrt(x**2 + y**2), 0, SPEED)
        if magnitude > DEADZONE:
            left = magnitude * (sin(theta) + cos(theta) / TURN_DAMPENING)
            right = magnitude * (sin(theta) - cos(theta) / TURN_DAMPENING)
            radio.send("{},{}".format(int(left),int(right)))
            x_index = map_range(x, -505, 505, 0, 4)
            y_index = map_range(y, -505, 505, 0, 4)
            display.clear()
            display.set_pixel(4-x_index, 4-y_index, 9)
            print(x, y, theta, magnitude, left, right)
        else:
            radio.send("0,0")


J = Joystickbit()
J.forever()

