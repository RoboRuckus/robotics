// Defines the robot class
class Robot {
  public:
  /* 
   *  Robot variables.
   *  Add things like wheel speeds and other .
   *  movement parameters here.
   */
    int playerNumber;
    String RobotName, botNum;

    // Initialize robot
    Robot (String name) : RobotName(name) {}

    // Called when a player is assigned to the robot
    void playerAssigned(int player){
      playerNumber = player;
    }

    /* 
     *  Called when the robot needs to turn.
     *  direction: 0 = right, 1 = left.
     */
    void turn(int direction, int magnitude){
      return;
    }

    // Called when the robot needs to drive forward
    void driveForward(int magnitude){
      return;
    }

    // Called when the robot needs to drive forward
    void driveBackward(int magnitude){
      return;
    }

    // Called when a robot is told to move, but is blocked
    void blockedMove() {
      return;
    }

    /* 
     *  Called when the robot takes damage.
     *  amount = total damage taken so far.
     */
    void takeDamage (int amount) {
      return;
    }

    /*
     * Called when a robot has new settings.
     * settings: a comma seprated list of new parameters.
     * commet: true when the settings should be saved to persistent storage like EEPROM.
     * Should also update robot movement parameter varibles with new values.
     */
    void saveSettings(String settings, bool commit) {
      return;
    }

    /*
     * Called when the robot neesd to load its settings.
     * Should return a JSON object of all the modifiable movement parameters.
     */
    String loadSettings(){
      String content = "{\"name\": \"" + RobotName + "\", \"controls\": [{ \"name\": \"LinearSpeedTarget\", \"displayname\": \"Speed of wheels\", \"min\": 50, \"max\": 150, \"increment\": 1, \"current\": 80},{ \"name\": \"TurnDistance\", \"displayname\": \"Turn distance\", \"min\": 0.1, \"max\": 1.2, \"increment\": 0.01, \"current\": 0.8}]}";
      return content;
    }

    // Runs a speed test to see if the robot drives straight
    void speedTest() {
      driveForward(3);
      delay(1000);
      driveBackward(3);
    }

    // Runs a navigation test to see how the robot performs
    void navigationTest() {
      driveForward(2);
      delay(1000);
      driveBackward(1);
      delay(1000);
      turn(1, 0);
      delay(1000);
      turn(1, 1);
      delay(500);
      turn(2, 0);
    }

    // Called when the game is reset
    void reset() {
      playerNumber = 0;
      return;
    }
};

// Defines the WiFi class
class WiFi {
  private:
    String server, port, ssid, pass;
    String connection = "AT+CIPSTART=1,\"TCP\",\"";
    HardwareSerial& wifi;
    Robot& bot;
    bool started = false;
    
    // Executes a move received by the bot
    void executeMove(uint8_t movement, uint8_t magnitude, uint8_t outOfTurn)
    {
    if (movement <= 3)
      {
        // Standard movement
        if (magnitude > 0)
        {
          switch (movement)
          {
            case 0:
              // Left
              bot.turn(1, magnitude);
              break;
            case 1:
              // Right
              bot.turn(0, magnitude);
              break;
            case 2:
              // Forward
              bot.driveForward(magnitude);
              break;
            case 3:
              // Backup
              bot.driveBackward(magnitude);
              break;
          }
        }
        else
        {
          // Robot trying to move, but is blocked
          bot.blockedMove();
          delay(1000);    
        }
      }
      // Non-movment command
      else 
      {
        switch(movement)
        {
          case 4:
            // Take damage
            bot.takeDamage(magnitude);
            break;
        }
        delay(1000);
      }
      // Forces a response to the server, resets the WiFi on fail
      bool success = true;
      do
      {
        // Ensure connection isn't already open
        sendCommand(F("AT+CIPCLOSE=1"), F("\nOK"));
        success = true;
        // Open TCP connection to server
        String response = sendCommand(connection, F("\nOK"));
        // Check for failure
        if (response.indexOf(F("FAIL")) != -1 || response.indexOf(F("ERROR")) != -1)
        {
          success = false;
        }
        else
        {
          // This should really be a POST request, but GET is more reliable
          String message = "GET /Bot/Done?bot=";
          message = message + bot.botNum + " HTTP/1.1\r\nHost: " + server + ":" + port + "\r\nConnection: close\r\n\r\n";
          String command = "AT+CIPSEND=1,";
          response = sendCommand(command + message.length(), F("\nOK"));
          if (response.indexOf(F("ERROR")) != -1)
          {
            Serial.println(F("Could not send message"));
            success = false;
          }
          else
          {
            // Notify server that bot has finished moving, check for acknowledgment
            response = sendCommand(message, F("AK\n"));
            if (response.indexOf(F("ERROR")) != -1)
            {
              success = false;
            }
          }
          if (!success)
          {
            // Something went wrong, try restarting the server on the WiFi module
            delay(350);
            sendCommand(F("AT+CIPMUX=1"), F("\nOK"));
            sendCommand(F("AT+CIPSERVER=1,8080"), F("\nOK"));
          }
        }
      } while (!success);
    }

    // Receives and prcesses commands while in setup mode
    void setupMode(String Message) {
      // Prase instruction
      int instruction = Message.substring(0, Message.indexOf(':')).toInt();

      // Check if a response is needed here
      if (instruction != 0) {
        // Respond and close the connection
        sendCommand(F("AT+CIPSEND=0,2"), F("\nOK"));
        sendCommand(F("OK"), F("CLOSED"));

        // Parse the message
        Message = Message.substring(Message.indexOf(':') + 1);
      }

      if (instruction == 0) 
      {
        // Load the settings
        String settings = bot.loadSettings();
        // Send the settings to the game server
        sendCommand("AT+CIPSEND=0," + String(settings.length()), F("\nOK"));
        sendCommand(settings, "CLOSED");
      }
      else if (instruction == 1) 
      {
        // Save the settings temporarily
        bot.saveSettings(Message, false);
        // Run a speed test
        bot.speedTest();
      }
      else if (instruction == 2) 
      {
        // Save the settings temporarily
        bot.saveSettings(Message, false);
        // Run a navigation test
        bot.navigationTest();
      }
      else if (instruction == 3) 
      {
        // Save the settings persistently and exit setup mode
        bot.saveSettings(Message, true);
        inSetupMode = false;
      }     
    }
    
  public:
    bool inSetupMode = false;

    // Intialize the WiFi object with all necessary info
    WiFi(HardwareSerial& SerialPort, String ServerIP, String ServerPort, String SSID, String WPA_Pass, Robot& Bot)
    : wifi(SerialPort)
    , server(ServerIP)
    , port(ServerPort)
    , ssid(SSID)
    , pass(WPA_Pass)
    , bot(Bot)
    {
      // Build the connection string
      connection = connection + server + "\"," + port;
    }

    // Sets up the robot, connecting to the Wi-Fi, informing the server of itself, and so on.
    bool Startup() {
          // Empty buffer
          while (wifi.available())
          {
            wifi.read(); // Read the next character
          }
        
          // Enable multiplexing (necessary for server operations)
          sendCommand(F("AT+CIPMUX=1"), F("\nOK"));
          
          // Stop server just in case
          sendCommand(F("AT+CIPSERVER=0"), F("\nOK"));
        
          // Initialize radio
          sendCommand(F("AT+CWMODE=1"), F("\nOK"));
        
          // Disable DHCP server
          sendCommand(F("AT+CWDHCP=1,1"), F("\nOK"));  
          
          // Restart the module to enable changes
          sendCommand(F("AT+RST"), F("ready"));
          
          // Enable multiplexing (necessary for server operations)
          sendCommand(F("AT+CIPMUX=1"), F("\nOK"));
          
          // Join WiFi network
          //sendCommand("AT+CWJAP_CUR=\"" + ssid + "\",", F("\nOK"));
        
          // Swap this with the above line for an unprotected network
          sendCommand("AT+CWJAP_CUR=\"" + ssid + "\",\"" + pass + "\"", F("\nOK"));
        
          // Get assigned IP address
          wifi.println(F("AT+CIPSTA?"));
          wifi.find("ip:\"");
          String client = wifi.readStringUntil('"');
          // Empty buffer
          while (wifi.available())
          {
            wifi.read(); // Read the next character
          }
          
          // Start server
          sendCommand(F("AT+CIPSERVER=1,8080"), F("\nOK"));
          
          // Connect to server
          sendCommand(connection, F("\nOK"));
          delay(200);
        
          // Inform server of bot
          String message = "GET /Bot/Index?ip=";
          message = message + client + "&name=" + bot.RobotName + " HTTP/1.1\r\nHost: " + server + ":" + port + "\r\nConnection: close\r\n\r\n";
          String command = "AT+CIPSEND=1,";
          sendCommand(command + message.length(), F("\nOK"));  
          String response = sendCommand(message, F("AK\n"));
          if (response.indexOf(F("ERROR")) != -1)
          {
            return false;
          }        
          return true;
        }

        // Processes a message from the game server
        void MessageReceived (String message) {
          // Parse message to remove WiFi module preamble
          message = message.substring(message.indexOf(":") + 1);
          // Check if game is already started
          if (started)
          {
            // Parse movement instruction
            uint8_t movement = message[0] - '0';   // Convert char to int
            uint8_t magnitude = message[1] - '0';  // Convert char to int
            uint8_t outOfTurn = message[2] - '0';  // Convert char to int
            if (outOfTurn == 2)
            {
              // Bot received reset command
              started = false;
              bot.reset();
            }
            else
            {
              // Bot received move order
              executeMove(movement, magnitude, outOfTurn);
            }
          }
          // Check if in setup mode
          else if (inSetupMode)
          {
            setupMode(message);            
          }
          else
          {
            // Prase instruction, has the format instruction:message
            int instruction = message.substring(0, message.indexOf(':')).toInt();
            // Bot has been assigned to player
            if (instruction == 0)
            {
              // Parse message
              message = message.substring(message.indexOf(':') + 1);
              // Get assigned player
              bot.playerAssigned(message[0] - '0');
              // Get assigned bot number
              bot.botNum = message.substring(1, message.indexOf('\n'));
              started = true;
            }
            else if (instruction == 1)
            {
              // Enter setup mode
              inSetupMode = true;
            }
          }
      }

      /* Send command to WiFi module
      * command is the command to send (blank for read data back)
      * EoT is the End of Tranmission string that indicates
      * to stop reading. ERROR will always terminate.
      * If EoT is an empty string, the command will be sent
      * but the method won't wait for a response.
      * The method will timeout after ~8 seconds of not finding EoT or ERROR
      */
      String sendCommand(String command, String EoT) {
        String response = "";
        // Check if sending a command
        if (command != F(""))
        {
          // Send command
          wifi.println(command);
          delay(5);
        }
        // Check if reading from module
        if (EoT != F(""))
        {
          int i = 0;
          // Read until the end EoT string is found, or timeout
          while (response.indexOf(F("ERROR")) == -1 && response.indexOf(EoT) == -1 && i < 8000)
          {
            while (wifi.available())
            {
              // Read from moduel
              response += (char)wifi.read();
            }
            i++;
            delay(1);
          }
          if (i == 8000)
          {
            // Timed out
            return F("ERROR");
          }
      }
      return response;
    }
};

// Varibles for initializing the robot and WiFi module
String SSID = "RoboRuckus";
String WPA_Pass = "Password";
String IP = "192.168.3.1";
String Port = "8082";
String RobotName = "Test%20Bot";

// Create robot object
Robot bot = Robot(RobotName);
// Create wifi object
WiFi wifi = WiFi(Serial, IP, Port, SSID, WPA_Pass, bot);

void setup() {
  // Start the serial connection
  Serial.begin(115200);
  // Initialize the WiFi module and connect to server
  while (!wifi.Startup()) {
    delay(1000);
  }
}

void loop() {
  if (Serial.available()) // Check if the WiFi has a message
    {
      if (Serial.find("+IPD,0,")) // Check if it's a message from the server
      {
        // Read message, should be terminated by \n (new line) character
        String message = Serial.readStringUntil('\n');
        // Check if in setup mode
        if (!wifi.inSetupMode){
          // Respond and close the connection
          wifi.sendCommand(F("AT+CIPSEND=0,2"), F("\nOK"));
          wifi.sendCommand(F("OK"), F("CLOSED"));
        }
        // Pass message to WiFi object for processing
        wifi.MessageReceived(message);
      }
      else
      {
        // Empty the buffer
        while (Serial.available()) {
          Serial.read(); // Read the next character
        }
      }
    }
}
