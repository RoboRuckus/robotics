#Maqueen:Plus hardware and I2C definitions: MIT Lesser General Public License Copyright (c) 2010-2020 DFRobot Co.Ltd (http://www.dfrobot.com)
#uPython module: MIT Lesser General Public License Copyright (c) 2021 Technology Alliance Group NW (https://tagnw.org)
#Contributors: ShipShupe

from microbit import i2c, display, Image, sleep, button_a, button_b, compass
import struct
import radio
import time
from math import pi as PI, modf

I2caddr = 0x10

RADIO_GROUP = 1

#Motor Index Constants
RIGHT = 1
LEFT = 2
ALL = 0

def clamp(x, xmin, xmax):
    return max(xmin, min(x, xmax))

class Colors:
    Red = 1
    Green = 2
    Yellow = 3
    Blue = 4
    Purple = 5
    Cyan = 6
    White = 7

class Servos:
    S1 = 0x14
    S2 = 0x15
    S3 = 0x16

class MaqueenPlus:

    version = None
    running = False
    RadioGroup = RADIO_GROUP
    speed_left = 60
    speed_right = 60
    speed = 60
    wheelDiameter = 44
    quarterTurn = 0.35
    fullMove = .75
    hold_heading = None

    PID = False

    controls = None

    def __init__(self):
        self.I2CInit()
        self.RGB(Colors.White, Colors.White)
        self.LRCorrection = 1
        self.PID = self.getPID()
        self.controls = {"F": (self.forward, Image.ARROW_N),
                         "B": (self.backward, Image.ARROW_S),
                         "R": (self.right90, Image.ARROW_W),
                         "L": (self.left90, Image.ARROW_E),
                         "P": (self.togglePID, "P")}
        radio.config(group=RADIO_GROUP)
        radio.on()

    def forever(self):
        self.running = True
        radio.on()
        radio.config(group=1)
        while self.running:
            sleep(20)

            #Disable if worried about gamification and chaos. Otherwise, enjoy!
            if button_a.was_pressed():
                self.setRadio(-1)
            elif button_b.was_pressed():
                self.setRadio(1)

            data = radio.receive()
            if data is None:
                display.show(Image.HAPPY)
                continue
            elif data in self.controls:
                print(data)
                display.show(self.controls[data][1])
                self.controls[data][0]()
            elif "," in data:
                m_data = data.split(',')
                self.setMotors(int(m_data[0]),int(m_data[1]))
            else:
                display.show(Image.HAPPY)

    def getVersion(self):
        i2c.write(0x10, bytearray([0x32]))
        sleep(100)
        return i2c.read(0x10, 1)

    def I2CInit(self):
        display.show('X')
        while not self.version:
            sleep(1000)
            self.version = self.getVersion()
        display.show(Image.HAPPY)

    def setRadio(self, increment):
        self.RadioGroup = clamp(self.RadioGroup + increment, 1, 9)
        radio.off()
        radio.config(group=self.RadioGroup)
        radio.on()
        display.show(self.RadioGroup)
        sleep(500)

    #input something from Color class
    def RGB(self, colorL, colorR):
        buf = bytearray([0x0b, colorL, colorR])
        i2c.write(I2caddr, buf)

    def setMotors(self, speedL, speedR):
        dirL = 1 if speedL > 0 else 2
        dirR = 1 if speedR > 0 else 2
        buf = bytearray([0x00, dirL, abs(speedL), dirR, int(abs(speedR) * self.LRCorrection)])
        i2c.write(I2caddr, buf)

    def getPID(self):
        i2c.write(0x10, bytearray([0x0a]))
        sleep(100)
        return struct.unpack('B', i2c.read(0x10, 1))[0] == 1

    def togglePID(self):
        self.PID = not self.PID
        i2c.write(I2caddr, bytearray([0x0a,self.PID]))

    def calibrateMotors(self):
        self.LRCorrection = 1
        self.clearDistance(ALL)
        sample = self.getEncoderTicks()
        sample = (1,2) if sample == (0,0) else sample
        start = time.ticks_ms()
        timeout = time.ticks_add(start, 5000)
        loop = 0
        while sample[0]/sample[1] != 1 or time.ticks_ms() < timeout:
            self.clearDistance(ALL)
            for s in (40, -40):
                self.setMotors(s, s)
                sleep(500)
                self.setMotors(0,0)
                sleep(500)
                sample = self.getEncoderTicks()
                if sample[0] >= sample[1]:
                    self.LRCorrection += modf(sample[0]/sample[1])[0]
                else:
                    self.LRCorrection -= (1 - modf(sample[0]/sample[1])[0])
        self.clearDistance(ALL)

    def getServo(self,servo):
        i2c.write(0x10, bytearray(servo))
        return struct.unpack('>B', i2c.read(I2caddr, 1))[0]

    #Servo: pass e.g. Servo.S1
    def setServo(self, servo, angle):
        current = self.getServo(servo)
        while abs(current - angle) > 3 :
            current = int((angle * 0.05) + (current * 0.95))
            i2c.write(0x10, bytearray([servo,current]))
            sleep(10)

    def left90(self):
        before = self.getRotations(LEFT)
        self.RGB(Colors.Yellow, Colors.Red)
        self.setMotors(-self.speed, self.speed)
        while self.getRotations(LEFT) < before + self.quarterTurn:
            sleep(10)
        self.stopAll()

    def right90(self):
        before = self.getRotations(LEFT)
        self.RGB(Colors.Red, Colors.Yellow)
        self.setMotors(self.speed, -self.speed)
        while self.getRotations(LEFT) < before + self.quarterTurn:
            sleep(10)
        self.stopAll()

    def forward(self):
        before = self.getDistance(LEFT)
        self.RGB(Colors.Green, Colors.Green)
        self.setMotors(self.speed, self.speed)
        while self.getDistance(LEFT) < before + 150:
            sleep(10)
        self.stopAll()

    def backward(self):
        before = self.getDistance(LEFT)
        self.RGB(Colors.White, Colors.White)
        self.setMotors(-self.speed, -self.speed)
        while self.getDistance(LEFT) < before + 150:
            sleep(10)
        self.stopAll()

    def stopAll(self):
        self.setMotors(0,0)
        self.RGB(Colors.White, Colors.White)


    # direction parameters:1=left motor;2=right motor
    # Get the motor speed
    def motorSpeed(self, direction):
        buf = bytearray(1)
        buf[0] = 0
        i2c.write(I2caddr, buf)
        motorSpeed_d = struct.unpack('>BBBB', i2c.read(I2caddr, 8))
        if direction == 1:
            return motorSpeed_d[1]
        elif direction == 2:
            return motorSpeed_d[3]

    # Get the motor direction
    # State:0=stop;1=forward;2=reverse
    def motorState(self, direction):
        i2c.write(I2caddr, bytearray([0x00]))
        motorSpeed_d = struct.unpack('>BBBB', i2c.read(I2caddr, 8))
        if direction == 1:
            return motorSpeed_d[0]
        elif  direction == 2:
            return motorSpeed_d[2]

    def clearDistance(self, motor = ALL):
        addr = 0x04 if motor in (ALL, LEFT) else 0x06
        buf = bytearray([addr, 0,0,0]) if motor is ALL else bytearray([addr, 0])
        i2c.write(0x10, buf)

    #(Left,Right) doesn't care which direction
    def getEncoderTicks(self):
        i2c.write(0x10, bytearray([0x04]))
        buf = i2c.read(0x10, 4)
        return (buf[0]<<8|buf[1], buf[2]<<8|buf[3])

    def getRotations(self, motor_side):
        i2c.write(0x10, bytearray([0x04]))
        sleep(10)
        buf = i2c.read(0x10, 4)
        if motor_side == LEFT:
            distance = (((buf[0]<<8)|buf[1]) * 10)/900
        else:
            distance = (((buf[2]<<8)|buf[3]) * 10)/900
        return distance

    #Whatever units wheelDiameter is in
    def getDistance(self, motor_side):
        return self.getRotations(motor_side) * self.wheelDiameter * PI

    #Returns [L3, L2, L1, R1, R2, R3]
    def getLine(self):
        i2c.write(0x10, bytearray([0x1D]))
        line_d = struct.unpack('b', i2c.read(I2caddr, 1))
        return [(line_d[0] & 0x01) == 1, (line_d[0] & 0x02) == 2, (line_d[0] & 0x04) == 4,
                (line_d[0] & 0x08) == 8, (line_d[0] & 0x10) == 16, (line_d[0] & 0x20) == 32]

    def getLineGrayscale(self):
        buf[0] = 0x1E
        i2c.write(I2caddr, bytearray([0x1e]))
        return struct.unpack('>HHHHHH', i2c.read(I2caddr, 12))


M = MaqueenPlus()
M.forever()
