# Initialize Maqueen
DFRobotMaqueenPlus.i2c_init()
DFRobotMaqueenPlus.PID(PID.OFF)

#Change LED color here
DFRobotMaqueenPlus.set_rgb_light(RGBLight.RGBA, Color.BLUE)

# Change movement timings here
LinearSpeedTarget = 95
LinearTime = 1300
LinearDistance = 0.72
TurnDistance = 0.32

# Change robot name here (must be URL escaped)
RobotName = "Test%20Bot"

# Change server info here
ServerAddress = "192.168.3.1"
ServerPort = "8082"

# Change Wi-Fi credentials here
SSID = "RoboRuckus"
WPA_Pass = "Ruckus_c0d3"

# Initialize variables, nothing to change from here on
Left_Forward_Speed = 33
Left_Backward_Speed = 33
Right_Forward_Speed = 33
Right_Backward_Speed = 33
ConnectionString = "AT+CIPSTART=1,\"TCP\",\"" + ServerAddress + "\"," + ServerPort
BotNumber = "0"
Assigned = False
PlayerNumber = 0

# Set UART buffers to something reasonable
serial.set_rx_buffer_size(255)
serial.set_tx_buffer_size(255)

# Enable serial conenction to ESP8266
serial.redirect(SerialPin.P1, SerialPin.P2, BaudRate.BAUD_RATE115200)

# Ensure ESP8266 is at 115200, not needed for most modules
# serial.write_string("AT+UART_DEF=115200,8,1,0,0" + "\u000D" + "\u000A")
# serial.set_baud_rate(BaudRate.BAUD_RATE115200)

# Bind button functions
input.on_button_pressed(Button.A, CalibrateSpeed)
input.on_button_pressed(Button.B, TestPattern)

# Start WiFi connection
basic.pause(1000)
music.set_volume(255)
while (not WifiStartup()):
    basic.show_icon(IconNames.SAD)
    basic.pause(1000)
basic.show_icon(IconNames.HAPPY)

# Parse a received message from the server
def MessageReceived(message: str):
    global Assigned, PlayerNumber, BotNumber
    message = message.substr(message.index_of(":") + 1)
    if Assigned:
        # Parse message
        Movement = parseInt(message.char_at(0))
        Magnitude = parseInt(message.char_at(1))
        OutOfTurn = parseInt(message.char_at(2))

        # Check for reset command
        if OutOfTurn == 2:
            Assigned = False
            basic.show_icon(IconNames.HAPPY)
        else:
            # Process a move order
            ProcessMove(Movement, Magnitude, OutOfTurn)
    else:
        #Process an instruction
        ReceivedString = message.substr(0, message.index_of(":"))
        Instruction = parseInt(ReceivedString);
        if Instruction == 0:
            # Get player assignment
            message = message.substr(message.index_of(":") + 1)
            PlayerNumber = parseInt(message.char_at(0))
            # Get bot number
            BotNumber = message.char_at(1)
            basic.show_number(PlayerNumber)
            Assigned = True
        elif Instruction == 1:
            # Setup/tuning mode not implemented yet
            pass

# Process and execute a move order
def ProcessMove(Movement: int, Magnitude: int, OutOfTurn: int):
    if Movement <= 3:
        # Standard movement
        if Magnitude > 0:
            if Movement == 0:
                # Left
                Turn(Magnitude, 1)
            elif Movement == 1:
                # Right
                Turn(Magnitude, 0)
            elif Movement == 2:
                # Forward
                LinearMove(Magnitude, 0, False)
            elif Movement == 3:
                # Backup
                LinearMove(Magnitude, 1, False)
        else:
            # Robot trying to move, but is blocked
            basic.show_icon(IconNames.CONFUSED)
            soundExpression.sad.play_until_done()
    # Non-movment command
    else:
        if Movement == 4:
            #Damage taken
            basic.show_icon(IconNames.SURPRISED)
            soundExpression.sad.play_until_done()
    # Forces a response to the server, resets the WiFi on fail
    success = False
    while not success:
        # Ensure connection isn't already open
        SendCommand("AT+CIPCLOSE=1", "")
        success = True;
        # Open TCP connection to server
        response = SendCommand(ConnectionString, "OK");
        if response.includes("FAIL") or response.includes("ERROR"):
            success = False;
        else:
            # This should really be a POST request, but GET is more reliable
            message = "GET /Bot/Done?bot=";
            message = message + BotNumber + " HTTP/1.1"+ "\u000D" + "\u000A" + "Host: " + ServerAddress + ":" + ServerPort + "\u000D" + "\u000A" + "Connection: close" + "\u000D" + "\u000A" + "\u000D" + "\u000A";
            command = "AT+CIPSEND=1,";
            response = SendCommand(command + str(len(message) + 2), "OK");

            if response.includes("ERROR"):
                success = False;
            else:
                # Notify server that bot has finished moving, check for acknowledgment
                response = SendCommand(message, "AK")
            if response.includes("ERROR"):
                success = False
        if not success:
            # Something went wrong, try resetting the WiFi module
            basic.pause(350)
            SendCommand("AT+CIPMUX=1", "OK")
            SendCommand("AT+CIPSERVER=1,8080", "OK")
    basic.show_number(PlayerNumber)

def WifiStartup():
    # Empty Buffer
    EmptySerialBuffer()

    # Enable multiplexing (necessary for server operations)
    SendCommand("AT+CIPMUX=1", "OK")

    # Stop server just in case
    SendCommand("AT+CIPSERVER=0", "OK")

    # Initialize radio
    SendCommand("AT+CWMODE=1", "OK")

    # Disable DHCP server
    SendCommand("AT+CWDHCP=1,1", "OK")

    # Restart the module to enable changes
    SendCommand("AT+RST", "ready")
    basic.pause(1000)

    # Enable multiplexing (necessary for server operations)
    SendCommand("AT+CIPMUX=1", "OK")

    # Join WiFi network
    # SendCommand("AT+CWJAP=\"" + SSID + "\",", "OK")
    # Swap the below with the above line for an  unprotected network
    SendCommand("AT+CWJAP_CUR=\"" + SSID + "\",\"" + WPA_Pass + "\"", "OK")

    # Get assigned IP address
    serial.write_string("AT+CIPSTA?" + "\u000D" + "\u000A")
# null is discarded, just needed to read until the start of the IP string
    null = serial.read_until("\"")
    client = serial.read_until("\"")

    # Empty Buffer
    EmptySerialBuffer()

    # Start server
    SendCommand("AT+CIPSERVER=1,8080", "OK")

    # Connect to server
    SendCommand(ConnectionString, "OK")
    basic.pause(200)

    # Inform server of bot
    message = ""
    message = "GET /Bot/Index?ip=" + client + "&name=" + RobotName + " HTTP/1.1" + "\u000D" + "\u000A" + "Host: " + ServerAddress + ":" + ServerPort + "\u000D" + "\u000A" + "Connection: close" + "\u000D" + "\u000A" + "\u000D" + "\u000A"
    SendCommand("AT+CIPSEND=1," + str(len(message) + 2), "OK")
    response = SendCommand(message, "AK")

    # Check for server acknowledgment
    if response.includes("ERROR"):
        return False
    return True

# Sends an AT command to the ESP8266
# Will return immdiately with "OK" unless an EndString is supplied
# then it will wait until that string is found in the response or
# error if it's not found.
# If no command is supplied, will just read a response.
def SendCommand(Command: str, EndString: str):
    serial_str: str = ""
    if Command != "":
        # Send command
        serial.write_string(Command + "\u000D" + "\u000A")
        basic.pause(100)
    if EndString != "":
        time = input.running_time()
        # Look for EndString or other common response
        while True:
            # Prevent the string from getting too long
            serial_str += serial.read_string()
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

# Attempts to empty any data left in the serial buffer
def EmptySerialBuffer():
    ser_buffer = serial.read_string()
    while len(ser_buffer) > 0:
        ser_buffer = serial.read_string()

# Main loop
def on_forever():
    received = ""
    receive_buf = serial.read_string()
    # Check for data on the serial port
    if len(receive_buf) > 0:
        while len(receive_buf) > 0:
            received += receive_buf
            receive_buf = serial.read_string()
        # Check if it's from the server
        if received.includes("+IPD,0,"):
            # Send acknowledgment
            SendCommand("AT+CIPSEND=0,2", "OK")
            SendCommand("OK", "CLOSED")
            EmptySerialBuffer()
            # Process received message
            MessageReceived(received)
    basic.pause(1)
basic.forever(on_forever)

# Move forward or backward
def LinearMove(Magnitude: int, MoveDirection: int, Calibrate: bool):
    global Right_Forward_Speed, Right_Backward_Speed, Left_Forward_Speed, Left_Backward_Speed
    # Clear motor distance
    DFRobotMaqueenPlus.clear_distance(Motors.ALL)
    # Calculate total move disatnce
    total = LinearDistance + ((LinearDistance + 0.18) * (Magnitude - 1))
    # Calculate upper-bound of move time
    total_time = LinearTime * Magnitude
    # Set initial motor speeds
    right_motor = 0
    left_motor =  0
    # Get target motor speeds
    left_target = Left_Forward_Speed
    right_target = Right_Forward_Speed
    # Set direction of move
    dir = Dir.CW
    # Wait for clear disatance to finish
    basic.pause(50)

    left_done = False
    right_done = False

    # Start upper-bound timer
    time = input.running_time()

    # Check if going backward
    if MoveDirection == 1:
        dir = Dir.CCW
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
        DFRobotMaqueenPlus.motot_run(Motors.M1, dir, left_motor)
        DFRobotMaqueenPlus.motot_run(Motors.M2, dir, right_motor)
        basic.pause(20)
    # Pause if calibrating to let motor speed stabilize
    if (Calibrate):
        basic.pause(350)
    
    # This loop will move the requested distance or exit on an upper-bound timeout
    while ((input.running_time() - time) <= total_time):
        # Get distance traveled
        left_distance = parse_float(DFRobotMaqueenPlus.reade_distance(Motors1.M1))
        right_distance = parse_float(DFRobotMaqueenPlus.reade_distance(Motors1.M2))
        # Check if move is done for each wheel
        if (not left_done and left_distance >= total):
            DFRobotMaqueenPlus.motot_stop(Motors.M1)
            left_done = True
        if (not right_done and right_distance >= total):
            DFRobotMaqueenPlus.motot_stop(Motors.M2)
            right_done = True
        # Check if all motors are done moving
        if (right_done and left_done):
            break
        
        # If calibrating, check wheel speeds as well
        if (Calibrate):
            left = DFRobotMaqueenPlus.read_speed(Motors1.M1)
            right = DFRobotMaqueenPlus.read_speed(Motors1.M2)
            if (not right_done and not left_done):
                # Check if right motor is going to fast or too slow and adjust
                if (right - LinearSpeedTarget > 5):
                    right_motor -= 1
                    DFRobotMaqueenPlus.motot_run(Motors.M2, dir, right_motor)
                    # Check which direction speed to adjust
                    if MoveDirection == 0:
                        Right_Forward_Speed = right_motor
                    elif MoveDirection == 1:
                        Right_Backward_Speed = right_motor
                elif (right - LinearSpeedTarget < -5):
                    right_motor += 1
                    DFRobotMaqueenPlus.motot_run(Motors.M2, dir, right_motor)
                    # Check which direction speed to adjust
                    if MoveDirection == 0:
                        Right_Forward_Speed = right_motor
                    elif MoveDirection == 1:
                        Right_Backward_Speed = right_motor
                # Check if left motor is going to fast or too slow and adjust
                if (left - LinearSpeedTarget > 5):
                    left_motor -= 1
                    DFRobotMaqueenPlus.motot_run(Motors.M1, dir, left_motor)
                    # Check which direction speed to adjust
                    if MoveDirection == 0:
                        Left_Forward_Speed = left_motor
                    elif MoveDirection == 1:
                        Left_Backward_Speed = left_motor
                elif (left - LinearSpeedTarget < -5):
                    left_motor += 1
                    DFRobotMaqueenPlus.motot_run(Motors.M1, dir, left_motor)
                    # Check which direction speed to adjust
                    if MoveDirection == 0:
                        Left_Forward_Speed = left_motor
                    elif MoveDirection == 1:
                        Left_Backward_Speed = left_motor
            #Pause to let new speed, if any, stabilize
            basic.pause(20)
    DFRobotMaqueenPlus.motot_stop(Motors.ALL)

# Turn (rotate) left or right
def Turn(magnitude: int, direction: int):
    for index in range (magnitude):
        # Clear wheels distances and wait for it to complete
        DFRobotMaqueenPlus.clear_distance(Motors.ALL)
        basic.pause(50)
        if direction == 0:
            # Turn right, motor must move a bit faster since other wheel is stationary
            DFRobotMaqueenPlus.motot_run(Motors.M1, Dir.CW, Left_Forward_Speed + 15)
            # Trun wheel required distance
            while parse_float(DFRobotMaqueenPlus.reade_distance(Motors1.M1)) < TurnDistance:
                basic.pause(1)
            DFRobotMaqueenPlus.motot_stop(Motors.ALL)
            # This clear is probably unnecessary since it was claered above, may remove
            DFRobotMaqueenPlus.clear_distance(Motors.M2)
            basic.pause(50)
            # Run other wheel backwards to complete turn
            DFRobotMaqueenPlus.motot_run(Motors.M2, Dir.CCW, Right_Backward_Speed + 15)
            while parse_float(DFRobotMaqueenPlus.reade_distance(Motors1.M2)) < TurnDistance:
                basic.pause(1)
        elif direction == 1:
            # Turn left, motor must move a bit faster since other wheel is stationary
            DFRobotMaqueenPlus.motot_run(Motors.M2, Dir.CW, Right_Forward_Speed + 15)
            while parse_float(DFRobotMaqueenPlus.reade_distance(Motors1.M2)) < TurnDistance:
                basic.pause(1)
            DFRobotMaqueenPlus.motot_stop(Motors.ALL)
            # This clear is probably unnecessary since it was claered above, may remove
            DFRobotMaqueenPlus.clear_distance(Motors.M1)
            basic.pause(50)
            # Run other wheel backwards to complete turn
            DFRobotMaqueenPlus.motot_run(Motors.M1, Dir.CCW, Left_Backward_Speed + 15)
            while parse_float(DFRobotMaqueenPlus.reade_distance(Motors1.M1)) < TurnDistance:
                basic.pause(1)
        DFRobotMaqueenPlus.motot_stop(Motors.ALL)
        basic.pause(250)

# Run the motors and calibrate their speeds
def CalibrateSpeed():
    serial.write_line("Calibrate")
    LinearMove(4, 0, True)
    basic.pause(1000)
    LinearMove(4, 1, True)

# Performs a test of the robot's movements
def TestPattern():
    LinearMove(2, 0, False)
    basic.pause(1000)
    LinearMove(1, 1, False)
    basic.pause(1000)
    Turn(1, 0)
    basic.pause(1000)
    Turn(1, 1)
    basic.pause(500)
    Turn(2, 0)
