# Maqueen:Plus hardware and I2C definitions: MIT Lesser General Public License Copyright (c) 2010-2020 DFRobot Co.Ltd (http://www.dfrobot.com)
# uPython module: MIT Lesser General Public License Copyright (c) 2021 Technology Alliance Group NW (https://tagnw.org)
# Contributors: ShipShupe, Sam Groveman

from microbit import pin1, pin2, i2c, display, Image, sleep, uart, running_time, audio, Sound, button_a
import struct
import os
from math import pi as PI

# Change server info here
ServerAddress = "192.168.3.1"
ServerPort = "8082"

# Change Wi-Fi credentials here
SSID = "RoboRuckus"
WPA_Pass = "idontevenknowourwifi"

# Robot color
Color = 7

# class Colors:
#    Red = 1
#    Green = 2
#    Yellow = 3
#    Blue = 4
#    Purple = 5
#    Cyan = 6
#    White = 7

# Movement timings
LinearSpeedTarget = 100
LinearTime = 1300
LinearDistance = 0.72
TurnDistance = 0.32

# Robot name (must be URL escaped)
RobotName = "Test%20Bot"

# Initialize variables
Left_Forward_Speed = 40
Left_Backward_Speed = 40
Right_Forward_Speed = 40
Right_Backward_Speed = 40
ConnectionString = "AT+CIPSTART=1,\"TCP\",\"" + ServerAddress + "\"," + ServerPort
BotNumber = "0"
Assigned = False
PlayerNumber = 0
InSetupMode = False

class Dir:
    CW = 1
    CCW = 2

# Maqueen I2C address
I2caddr = 0x10

# Motor Index Constants
RIGHT = 1
LEFT = 2
ALL = 0

class WiFi:
    def __init__(self, ssid, pw, bot = None):
        uart.init(baudrate=115200, bits=8, parity=None, stop=1, tx=pin1, rx=pin2)
        self.bot = bot
        self.bot.LoadSettings(True)
        while (not self.WifiStartup()):
            display.show(Image.SAD)
            sleep(1000)
        display.show(Image.HAPPY)

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
        ip_string = self.SendCommand("AT+CIPSTA?", "gateway")
        if not(ip_string is None) and not ("ERROR" in ip_string):
            # Parse IP address
            ip_string = ip_string[ip_string.find("\"") + 1:]
            client = ip_string[0:ip_string.find("\"")]

            # Empty Buffer
            self.EmptySerialBuffer()

            # Start server
            self.SendCommand("AT+CIPSERVER=1,8080", "OK")

            # Connect to server
            self.SendCommand(ConnectionString, "OK")
            sleep(200)

            # Inform server of bot
            message = ""
            message = "GET /Bot/Index?ip=" + client + "&name=" + RobotName + " HTTP/1.1" + "\r\n" + "Host: " + ServerAddress + ":" + ServerPort + "\r\n" + "Connection: close" + "\r\n\r\n"
            self.SendCommand("AT+CIPSEND=1," + str(len(message) + 2), "OK")
            response = self.SendCommand(message, "AK")

            # Check for server acknowledgment
            if "ERROR" in response:
                return False
        else:
            return False
        return True

    def MessageReceived(self, message: str):
        global Assigned, PlayerNumber, BotNumber, InSetupMode
        message = message[(message.find(":") + 1):]
        if Assigned:
            # Parse message
            Movement = int(message[0])
            Magnitude = int(message[1])
            OutOfTurn = int(message[2])

            # Check for reset command
            if OutOfTurn == 2:
                Assigned = False
                display.show(Image.HAPPY)
            else:
                # Process a move order
                self.ProcessMove(Movement, Magnitude, OutOfTurn)
        elif InSetupMode:
            self.SetupMode(message)
        else:
            # Process an instruction
            instruction = int(message[0:message.find(":")])
            if instruction == 0:
                # Get player assignment
                message = message[message.find(":") + 1:]
                PlayerNumber = int(message[0])
                # Get bot number
                BotNumber = message[1]
                display.show(PlayerNumber)
                Assigned = True
            elif instruction == 1:
                display.show(Image.DUCK)
                InSetupMode = True

    def ProcessMove(self, Movement: int, Magnitude: int, OutOfTurn: int):
        if Movement <= 3:
            # Standard movement
            if Magnitude > 0:
                if Movement == 0:
                    # Left
                    self.bot.Turn(Magnitude, 1)
                elif Movement == 1:
                    # Right
                    self.bot.Turn(Magnitude, 0)
                elif Movement == 2:
                    # Forward
                    self.bot.LinearMove(Magnitude, 0, False)
                elif Movement == 3:
                    # Backup
                    self.bot.LinearMove(Magnitude, 1, False)
            else:
                # Robot trying to move, but is blocked
                display.show(Image.CONFUSED)
                audio.play(Sound.SAD, True)
        # Non-movment command
        else:
            if Movement == 4:
                # Damage taken
                display.show(Image.SURPRISED)
                audio.play(Sound.SAD, True)
        # Forces a response to the server, resets the WiFi on fail
        sleep(500)
        success = False
        while not success:
            # Ensure connection isn't already open
            self.SendCommand("AT+CIPCLOSE=1", "")
            success = True
            # Open TCP connection to server
            response = self.SendCommand(ConnectionString, "OK")
            if "FAIL" in response or "ERROR" in response:
                success = False
            else:
                # This should really be a POST request, but GET is more reliable
                message = "GET /Bot/Done?bot="
                message = message + BotNumber + " HTTP/1.1"+ "\r\n" + "Host: " + ServerAddress + ":" + ServerPort + "\r\n" + "Connection: close" + "\r\n\r\n"
                response = self.SendCommand("AT+CIPSEND=1," + str(len(message) + 2), "OK")

                if "ERROR" in response:
                    success = False
                else:
                    # Notify server that bot has finished moving, check for acknowledgment
                    response = self.SendCommand(message, "AK")
                if "ERROR" in response:
                    success = False
            if not success:
                # Something went wrong, try resetting the WiFi module
                sleep(350)
                self.SendCommand("AT+CIPMUX=1", "OK")
                self.SendCommand("AT+CIPSERVER=1,8080", "OK")
        display.show(PlayerNumber)

    # Setup and tuning mode
    def SetupMode(self, message: str):
        global InSetupMode
        instruction = int(message[0:message.find(":")])
        message = message[message.find(":") + 1:]
        # Respond and close the connection if no further response needed
        if instruction != 0:
            self.SendCommand("AT+CIPSEND=0,2", "OK")
            self.SendCommand("OK", "CLOSED")
            self.EmptySerialBuffer()

        # Send current settings to server
        if instruction == 0:
            settings = self.bot.LoadSettings()
            self.SendCommand("AT+CIPSEND=0," + str(len(settings)), "OK")
            self.SendCommand(settings, "CLOSED")
            self.EmptySerialBuffer()
        # Save new settings and run a calibration/speed test
        elif instruction == 1:
            self.bot.SaveSettings(message, False)
            self.bot.CalibrateSpeed()
        # Save new settings and run a navigation test
        elif instruction == 2:
            self.bot.SaveSettings(message, False)
            self.bot.NavigationTest()
        # Quit setup mode
        elif instruction == 3:
            # Save settings to storage
            self.bot.SaveSettings(message, True)
            InSetupMode = False
            display.show(Image.HAPPY)

    # Sends an AT command to the ESP8266
    # Will return immdiately with "OK" unless an EndString is supplied
    # then it will wait until that string is found in the response or
    # ERROR if it's not found.
    # If no command is supplied, will just read a response.
    def SendCommand(self, Command: str, EndString: str):
        serial_str = ""
        if Command != "":
            # Send command
            uart.write(bytes((Command + "\r\n"), "UTF-8"))
            sleep(100)
        if EndString != "":
            timeout = running_time()
            # Look for EndString or other common response
            while True:
                serial_buffer = uart.read()
                # Check if data was received
                if not(serial_buffer is None):
                    serial_str += str(serial_buffer, "UTF-8")
                # Prevent the string from getting too long
                if len(serial_str) > 300:
                    serial_str = serial_str[0:(len(serial_str) - 200)]
                # Check for EndString or other positive response
                if (EndString in serial_str) or ("ALREADY CONNECTED" in serial_str):
                    return serial_str
                # Check for error reponse
                elif ("ERROR" in serial_str) or ("SEND FAIL" in serial_str):
                    break
                if running_time() - timeout > 8000:
                    break
            return "ERROR"
        return "OK"

    # Attempts to empty any data left in the serial buffer
    def EmptySerialBuffer(self):
        ser_buffer = uart.read()
        while not(ser_buffer is None) and len(ser_buffer) > 0:
            ser_buffer = uart.read()

class MaqueenPlus:
    version = None
    running = False
    wheelDiameter = 44

    PID = False

    wifi = None

    def __init__(self):
        self.I2CInit()
        self.RGB(Color, Color)
        self.PID = self.getPID()
        self.wifi = WiFi(SSID, WPA_Pass, self)

    def forever(self):
        global InSetupMode
        self.running = True
        while self.running:
            if button_a.was_pressed():
                self.CalibrateSpeed()
            received = ""
            receive_buf = uart.read()
            # Check for data on the serial port
            if not(receive_buf is None):
                while not(receive_buf is None) and len(receive_buf) > 0:
                    received += str(receive_buf, "UTF-8")
                    receive_buf = uart.read()
                    sleep(2)
                # Check if it's from the server
                if "+IPD,0," in received:
                    if not InSetupMode:
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
        display.show(Image.NO)
        i2c.scan()
        while not self.version:
            sleep(1000)
            self.version = self.getVersion()
        display.show(Image.YES)

    def RGB(self, colorL, colorR):
        buf = bytearray([0x0b, colorL, colorR])
        i2c.write(I2caddr, buf)

    def setMotors(self, speedL, speedR, dirL, dirR):
        buf = bytearray([0x00, dirL, int(speedL), dirR, int(speedR)])
        i2c.write(I2caddr, buf)

    def setLMotor(self, speedL, dirL):
        buf = bytearray([0x00, dirL, int(speedL)])
        i2c.write(I2caddr, buf)

    def setRMotor(self, speedR, dirR):
        buf = bytearray([0x02, dirR, int(speedR)])
        i2c.write(I2caddr, buf)

    def stopAll(self):
        self.setMotors(0, 0, 0, 0)

    def getPID(self):
        i2c.write(0x10, bytearray([0x0a]))
        sleep(100)
        return struct.unpack('B', i2c.read(0x10, 1))[0] == 1

    def togglePID(self):
        self.PID = not self.PID
        i2c.write(I2caddr, bytearray([0x0a, self.PID]))

    # Motor parameters:1=left motor; 2=right motor
    # Get the motor speed
    def motorSpeed(self, motor):
        buf = bytearray(1)
        buf[0] = 0
        i2c.write(I2caddr, buf)
        motorSpeed_d = struct.unpack('>BBBB', i2c.read(I2caddr, 8))
        if motor == 2:
            return round(motorSpeed_d[1])
        elif motor == 1:
            return round(motorSpeed_d[3])

    def clearDistance(self, motor = ALL):
        addr = 0x04 if motor in (ALL, LEFT) else 0x06
        buf = bytearray([addr, 0, 0, 0]) if motor is ALL else bytearray([addr, 0])
        i2c.write(0x10, buf)

    def getRotations(self, motor_side):
        i2c.write(0x10, bytearray([0x04]))
        sleep(10)
        buf = i2c.read(0x10, 4)
        if motor_side == LEFT:
            distance = (((buf[0] << 8) | buf[1]) * 10)/900
        else:
            distance = (((buf[2] <<8 ) | buf[3]) * 10)/900
        return round(distance, 3)

    # Whatever units wheelDiameter is in
    def getDistance(self, motor_side):
        return self.getRotations(motor_side) * self.wheelDiameter * PI

    # Returns [L3, L2, L1, R1, R2, R3]
    def getLine(self):
        i2c.write(0x10, bytearray([0x1D]))
        line_d = struct.unpack('b', i2c.read(I2caddr, 1))
        return [(line_d[0] & 0x01) == 1, (line_d[0] & 0x02) == 2, (line_d[0] & 0x04) == 4,
                (line_d[0] & 0x08) == 8, (line_d[0] & 0x10) == 16, (line_d[0] & 0x20) == 32]

    # Move forward or backward
    def LinearMove(self, Magnitude: int, MoveDirection: int, Calibrate: bool):
        global Right_Forward_Speed, Right_Backward_Speed, Left_Forward_Speed, Left_Backward_Speed
        # Clear motor distance
        self.clearDistance(ALL)
        # Calculate total move disatnce
        total = LinearDistance + ((LinearDistance + 0.18) * (Magnitude - 1))
        # Calculate upper-bound of move time
        total_time = LinearTime * Magnitude
        # Set initial motor speeds
        right_motor = 0
        left_motor = 0
        # Get target motor speeds
        left_target = Left_Forward_Speed
        right_target = Right_Forward_Speed
        # Set direction of move
        direction = Dir.CW
        # Wait for clear disatance to finish
        sleep(50)

        left_done = False
        right_done = False

        # Start upper-bound timer
        time = running_time()

        # Check if going backward
        if MoveDirection == 1:
            direction = Dir.CCW
            left_target = Left_Backward_Speed
            right_target = Right_Backward_Speed

        # Slowly accelerate motors (prevents lurching on start)
        while right_motor < right_target or left_motor < left_target:
            if MoveDirection == 1:
                if Right_Backward_Speed - right_motor > 10:
                    right_motor += 10
                else:
                    right_motor += Right_Backward_Speed - right_motor

                if Left_Backward_Speed - left_motor > 10:
                    left_motor += 10
                else:
                    left_motor += Left_Backward_Speed - left_motor
            elif MoveDirection == 0:
                if Right_Forward_Speed - right_motor > 10:
                    right_motor += 10
                else:
                    right_motor += Right_Forward_Speed - right_motor

                if Left_Forward_Speed - left_motor > 10:
                    left_motor += 10
                else:
                    left_motor += Left_Forward_Speed - left_motor
            self.setMotors(left_motor, right_motor, direction, direction)
            sleep(20)
        # Pause if calibrating to let motor speed stabilize
        if (Calibrate):
            sleep(350)

        # This loop will move the requested distance or exit on an upper-bound timeout
        while ((running_time() - time) <= total_time):
            # Get distance traveled
            left_distance = float(self.getRotations(LEFT))
            right_distance = float(self.getRotations(RIGHT))
            # Check if move is done for each wheel
            if (not left_done and left_distance >= total):
                self.setLMotor(0, 0)
                left_done = True
            if (not right_done and right_distance >= total):
                self.setRMotor(0, 0)
                right_done = True
            # Check if all motors are done moving
            if (right_done and left_done):
                break

            # If calibrating, check wheel speeds as well
            if (Calibrate):
                left = self.motorSpeed(LEFT)
                right = self.motorSpeed(RIGHT)
                if (not right_done and not left_done):
                    # Check if right motor is going to fast or too slow and adjust
                    if (right - LinearSpeedTarget > 5):
                        right_motor -= 1
                        self.setRMotor(right_motor, direction)
                        # Check which direction speed to adjust
                        if MoveDirection == 0:
                            Right_Forward_Speed = right_motor
                        elif MoveDirection == 1:
                            Right_Backward_Speed = right_motor
                    elif (right - LinearSpeedTarget < -5):
                        right_motor += 1
                        self.setRMotor(right_motor, direction)
                        # Check which direction speed to adjust
                        if MoveDirection == 0:
                            Right_Forward_Speed = right_motor
                        elif MoveDirection == 1:
                            Right_Backward_Speed = right_motor
                    # Check if left motor is going to fast or too slow and adjust
                    if (left - LinearSpeedTarget > 5):
                        left_motor -= 1
                        self.setLMotor(left_motor, direction)
                        # Check which direction speed to adjust
                        if MoveDirection == 0:
                            Left_Forward_Speed = left_motor
                        elif MoveDirection == 1:
                            Left_Backward_Speed = left_motor
                    elif (left - LinearSpeedTarget < -5):
                        left_motor += 1
                        self.setLMotor(left_motor, direction)
                        # Check which direction speed to adjust
                        if MoveDirection == 0:
                            Left_Forward_Speed = left_motor
                        elif MoveDirection == 1:
                            Left_Backward_Speed = left_motor
                # Pause to let new speed, if any, stabilize
                sleep(20)
        self.stopAll()

    # Turn (rotate) left or right
    def Turn(self, magnitude: int, direction: int):
        for index in range(magnitude):
            # Clear wheels distances and wait for it to complete
            self.clearDistance(ALL)
            sleep(50)
            if direction == 0:
                # Turn right, motor must move a bit faster since other wheel is stationary
                self.setLMotor(Left_Forward_Speed + 15, Dir.CW)
                # Trun wheel required distance
                while float(self.getRotations(LEFT)) < TurnDistance:
                    sleep(1)
                self.stopAll()
                # This clear is probably unnecessary since it was claered above, may remove
                self.clearDistance(RIGHT)
                sleep(50)
                # Run other wheel backwards to complete turn
                self.setRMotor(Right_Backward_Speed + 15, Dir.CCW)
                while float(self.getRotations(RIGHT)) < TurnDistance:
                    sleep(1)
            elif direction == 1:
                # Turn left, motor must move a bit faster since other wheel is stationary
                self.setRMotor(Right_Forward_Speed + 15, Dir.CW)
                while float(self.getRotations(RIGHT)) < TurnDistance:
                    sleep(1)
                self.stopAll()
                # This clear is probably unnecessary since it was claered above, may remove
                self.clearDistance(LEFT)
                sleep(50)
                # Run other wheel backwards to complete turn
                self.setLMotor(Left_Backward_Speed + 15, Dir.CCW)
                while float(self.getRotations(LEFT)) < TurnDistance:
                    sleep(1)
            self.stopAll()
            sleep(250)

    # Saves new move settings, optionally writing them to storage.
    # If initialize is also true, will save a new file with the current settings
    def SaveSettings(self, NewSettings: str, commit: bool, initialize = False):
        global RobotName, LinearSpeedTarget, LinearTime, LinearDistance, TurnDistance, Color, Left_Forward_Speed, Left_Backward_Speed, Right_Forward_Speed, Right_Backward_Speed
        NewSettings = NewSettings[0:NewSettings.find(":")]
        # Assign new settings values
        settings = NewSettings.split(",")
        RobotName = settings[0]
        LinearSpeedTarget = int(settings[1])
        LinearTime = int(settings[2])
        LinearDistance = float(settings[3])
        TurnDistance = float(settings[4])
        Color = int(settings[5])
        self.RGB(Color, Color)

        # Load previous calibration settings on startup
        if initialize:
            Left_Forward_Speed = int(settings[6])
            Left_Backward_Speed = int(settings[7])
            Right_Forward_Speed = int(settings[8])
            Right_Backward_Speed = int(settings[9])
        else:
            NewSettings = NewSettings + "," + str(Left_Forward_Speed) + "," + str(Left_Backward_Speed) + "," + str(Right_Forward_Speed) + "," + str(Right_Backward_Speed) + ":"

        # Save new settings to file system
        if commit:
            # Write text file
            with open('settings.txt', 'w') as settings_file:
                settings_file.write(NewSettings)

    # Loads saved settings from storage
    def LoadSettings(self, initialize = False):
        global RobotName, LinearSpeedTarget, LinearTime, LinearDistance, TurnDistance, Color
        if not initialize:
            # Create JSON string from current settings
            content = '''{"name": "''' + RobotName + '''", "controls": [
            { "name": "LinearSpeedTarget", "displayname": "Speed", "min": 50, "max": 150, "increment": 1, "current": ''' + str(LinearSpeedTarget) + '''},
            { "name": "LinearTime", "displayname": "Max travel time (ms)", "min": 800, "max": 1500, "increment": 10, "current": ''' + str(LinearTime) + '''},
            { "name": "LinearDistance", "displayname": "Travel distance", "min": 0.2, "max": 1.2, "increment": 0.01, "current": ''' + str(LinearDistance) + '''},
            { "name": "TurnDistance", "displayname": "Turn distance", "min": 0.1, "max": 1.2, "increment": 0.01, "current": ''' + str(TurnDistance) + '''},
            { "name": "color", "displayname": "LED Color", "min": 1, "max": 7, "increment": 1, "current": ''' + str(Color) + '''}]}'''
            return content
        else:
            # Check if settings files exist, create it if not
            try:
                size = os.size("settings.txt")
            except:
                # Save default settings to files
                settings = RobotName + "," + str(LinearSpeedTarget) + "," + str(LinearTime) + "," + str(LinearDistance) + "," + str(TurnDistance) + "," + str(Color) + "," + str(Left_Forward_Speed) + "," + str(Left_Backward_Speed) + "," + str(Right_Forward_Speed) + "," + str(Right_Backward_Speed) + ":"
                self.SaveSettings(settings, True, True)
            else:
                # Load saved settings
                with open('settings.txt') as settings_file:
                    content = settings_file.readline()
                self.SaveSettings(content + ":", False, True)

    # Run the motors and calibrate their speeds
    def CalibrateSpeed(self):
        self.LinearMove(4, 0, True)
        sleep(1000)
        self.LinearMove(4, 1, True)

    # Performs a test of the robot's movements
    def NavigationTest(self):
        self.LinearMove(2, 0, False)
        sleep(1000)
        self.LinearMove(1, 1, False)
        sleep(1000)
        self.Turn(1, 0)
        sleep(1000)
        self.Turn(1, 1)
        sleep(500)
        self.Turn(2, 0)

M = MaqueenPlus()
M.forever()
