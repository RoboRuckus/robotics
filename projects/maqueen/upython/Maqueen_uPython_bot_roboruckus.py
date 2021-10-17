#Maqueen:Plus hardware and I2C definitions: MIT Lesser General Public License Copyright (c) 2010-2020 DFRobot Co.Ltd (http://www.dfrobot.com)
#uPython module: MIT Lesser General Public License Copyright (c) 2021 Technology Alliance Group NW (https://tagnw.org)
#Contributors: ShipShupe

from microbit import i2c, display, Image, sleep, button_a, button_b, compass, uart
import struct
import radio
import time
from math import pi as PI, modf

# Change movement timings here
LinearSpeedTarget = 100
LinearTime = 1300
LinearDistance = 0.72
TurnDistance = 0.32

# Change robot name here (must be URL escaped)
RobotName = "Test%20Bot"

# Change server info here
ServerAddress = "192.168.3.1"
ServerPort = "8082"

# Change Wi-Fi credentials here
SSID = "imawan"
WPA_Pass = "idontevenknowourwifi!"

# Initialize variables, nothing to change from here on
Left_Forward_Speed = 40
Left_Backward_Speed = 40
Right_Forward_Speed = 40
Right_Backward_Speed = 40
ConnectionString = "AT+CIPSTART=1,\"TCP\",\"" + ServerAddress + "\"," + ServerPort
BotNumber = "0"
Assigned = False
PlayerNumber = 0


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

class WiFi:

    def __init__(self, ssid, pw, bot = None):
        self.WifiStartup()
        self.bot = bot

    def WifiStartup(self):
        # Empty Buffer
        self.EmptySerialBuffer()

        # Enable multiplexing (necessary for server operations)
        self.SendCommand("AT+CIPMUX=1", "OK")

        # Stop server just in case
        self.SendCommand("AT+CIPSERVER=0", "OK")

        # Initialize radio
        self.SendCommand("AT+CWMODE=1", "OK")

        # Disable DHCP server
        self.SendCommand("AT+CWDHCP=1,1", "OK")

        # Restart the module to enable changes
        self.SendCommand("AT+RST", "ready")
        sleep(1000)

        # Enable multiplexing (necessary for server operations)
        self.SendCommand("AT+CIPMUX=1", "OK")

        # Join WiFi network
        # SendCommand("AT+CWJAP=\"" + SSID + "\",", "OK")
        # Swap the below with the above line for an  unprotected network
        self.SendCommand("AT+CWJAP_CUR=\"" + SSID + "\",\"" + WPA_Pass + "\"", "OK")

        # Get assigned IP address
        uart.write("AT+CIPSTA?" + "\u000D" + "\u000A")
        # null is discarded, just needed to read until the start of the IP string
        null = uart.read("\"")
        client = uart.read("\"")

        # Empty Buffer
        self.EmptySerialBuffer()

        # Start server
        self.SendCommand("AT+CIPSERVER=1,8080", "OK")

        # Connect to server
        self.SendCommand(ConnectionString, "OK")
        sleep(200)

        # Inform server of bot
        message = ""
        message = "GET /Bot/Index?ip=" + client + "&name=" + RobotName + " HTTP/1.1" + "\u000D" + "\u000A" + "Host: " + ServerAddress + ":" + ServerPort + "\u000D" + "\u000A" + "Connection: close" + "\u000D" + "\u000A" + "\u000D" + "\u000A"
        self.SendCommand("AT+CIPSEND=1," + str(len(message) + 2), "OK")
        response = self.SendCommand(message, "AK")

        # Check for server acknowledgment
        if response.includes("ERROR"):
            return False
        return True

    # Sends an AT command to the ESP8266
    # Will return immdiately with "OK" unless an EndString is supplied
    # then it will wait until that string is found in the response or
    # error if it's not found.
    # If no command is supplied, will just read a response.
    def SendCommand(self, Command, EndString: str):
        serial_str = ""
        if Command != "":
            # Send command
            uart.write(Command + "\u000D" + "\u000A")
            sleep(100)
        if EndString != "":
            time = input.running_time()
            # Look for EndString or other common response
            while True:
                # Prevent the string from getting too long
                serial_str += uart.read()
                if len(serial_str) > 300:
                    serial_str = serial_str.substr(len(serial_str) - 300)
                # Check for EndString or other positive response
                if serial_str.includes(EndString) or serial_str.includes("ALREADY CONNECTED"):
                    return serial_str
                # Check for error reponse
                elif serial_str.includes("ERROR") or serial_str.includes("SEND FAIL"):
                    break
                if input.running_time() - time > 10000:
                    break
            return "ERROR"
        return "OK"

    def MessageReceived(self, message: str):
        global Assigned, PlayerNumber, BotNumber
        message = message.substr(message.index_of(":") + 1)
        if Assigned:
            # Parse message
            Movement = int.from_bytes(message.char_at(0))
            Magnitude = int.from_bytes(message.char_at(1))
            OutOfTurn = int.from_bytes(message.char_at(2))

            # Check for reset command
            if OutOfTurn == 2:
                Assigned = False
                display.show(Image.HAPPY)
            else:
                # Process a move order
                self.bot.ProcessMove(Movement, Magnitude, OutOfTurn)
        else:
            #Process an instruction
            ReceivedString = message.substr(0, message.index_of(":"))
            Instruction = int.from_bytes(ReceivedString);
            if Instruction == 0:
                # Get player assignment
                message = message.substr(message.index_of(":") + 1)
                PlayerNumber = int.from_bytes(message.char_at(0))
                # Get bot number
                BotNumber = message.char_at(1)
                display.show(PlayerNumber)
                Assigned = True
            elif Instruction == 1:
                # Setup/tuning mode not implemented yet
                pass

    # Attempts to empty any data left in the serial buffer
    def EmptySerialBuffer():
        ser_buffer = uart.read()
        while len(ser_buffer) > 0:
            ser_buffer = uart.read()


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

    wifi = None

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
        self.wifi = WiFi(SSID, WPA_Pass, self)


    def forever(self):
        self.running = True
        while self.running:
            received = ""
            receive_buf = uart.read()
            # Check for data on the serial port
            if len(receive_buf) > 0:
                while len(receive_buf) > 0:
                    received += receive_buf
                    receive_buf = uart.read()
                # Check if it's from the server
                if received.includes("+IPD,0,"):
                    # Send acknowledgment
                    self.wifi.SendCommand("AT+CIPSEND=0,2", "OK")
                    self.wifi.SendCommand("OK", "CLOSED")
                    self.wifi.EmptySerialBuffer()
                    # Process received message
                    self.wifi.MessageReceived(received)
            sleep(20)

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
        i2c.write(I2caddr, bytearray([0x1e]))
        return struct.unpack('>HHHHHH', i2c.read(I2caddr, 12))


M = MaqueenPlus()
M.forever()
