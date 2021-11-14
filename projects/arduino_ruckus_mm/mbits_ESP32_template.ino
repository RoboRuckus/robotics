/*
 * Template for RoboRuckus game robot based on the 
 * ESP32 based Mbits board via Arduino platform.
 * https://www.elecrow.com/mbits.html
 *
 * External libraries needed:
 * FastLED https://github.com/FastLED/FastLED
 * Temperature_LM75_Derived: https://github.com/jeremycole/Temperature_LM75_Derived
 * Tone32: https://github.com/lbernstone/Tone32
 * MPU6050_tockn: https://github.com/Tockn/MPU6050_tockn
 *
 * Contributors: Sam Groveman
 */

#include "WiFi.h"
#include <Wire.h>
#include<EEPROM.h>
#include <FastLED.h>
//#include <Temperature_LM75_Derived.h>
#include <Tone32.h>
#include <MPU6050_tockn.h>

// Defines the robot class
class Robot {
  public:
  /* 
   *  Robot variables.
   *  Add things like wheel speeds and other
   *  movement parameters here.
   */
    int playerNumber = 0;
    String RobotName, botNum;
    
    int leftForwardSpeed, rightForwardSpeed, rightBackwardSpeed, leftBackwardSpeed;
    int robotColor = 0;

    enum class colors { Red, Green, Blue, Yellow, White, Putple, Orange };
    enum class images { Clear, One, Two, Three, Four, Five, Six, Seven, Eight, Nine, Happy, Sad, Surprised, Duck };

    // Initialize robot
    Robot(){}

    void begin(){
      Serial.println("Initializing robot");
      // Start LEDs
      FastLED.addLeds<WS2812B, 13, GRB>(leds, 25);
      FastLED.setBrightness(10);
      FastLED.clear();
      delay(50);
      FastLED.show();

      // Start IMU
      mpu6050.begin();
      mpu6050.calcGyroOffsets(true);
      Serial.println("");

      // Load settings from EEPROM
      EEPROM.begin(1024);
      RobotName = EEPROM.readString(0);

      // Load defaults if no settings in EEPROM yet
      if (RobotName == "")
      {
        RobotName = "Test%20Bot";
        leftForwardSpeed = 90;
        rightForwardSpeed = 90;
        leftBackwardSpeed = 90;
        rightBackwardSpeed = 90;
        robotColor = 0;
      } 
      else 
      {
        /*
         * Load remaining settings
         * Addresses are in bytes, int = 4 bytes
         * First 100 addresses (0-99) are reserved for name string
         */
        leftForwardSpeed = EEPROM.readInt(100);
        rightForwardSpeed = EEPROM.readInt(104);
        leftBackwardSpeed = EEPROM.readInt(108);
        rightBackwardSpeed = EEPROM.readInt(112);
        robotColor = EEPROM.readInt(116);
      }
    }
    
    // Called when a player is assigned to the robot
    void playerAssigned(int player){
      showImage((images)player, (colors)robotColor);
      playerNumber = player;
    }

    // Display an image in a color on the screen
    void showImage(images image, colors color){
      FastLED.clear();
      delay(10);
      Display(image_maps[(int)image], color_map[(int)color]);
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
      showImage(images::Surprised, (colors)robotColor);
      delay(1000);
      showImage((images)playerNumber, (colors)robotColor);
    }

    /* 
     *  Called when the robot takes damage.
     *  amount = total damage taken so far.
     */
    void takeDamage(int amount) {
      Serial.print(amount);
      showImage(images::Surprised, (colors)robotColor);
      delay(1000);
      showImage((images)playerNumber, (colors)robotColor);
    }

    /*
     * Called when a robot has new settings.
     * settings: a comma seprated list of new parameters.
     * commet: true when the settings should be saved to persistent storage like EEPROM.
     * Should also update robot movement parameter varibles with new values.
     */
    void saveSettings(String settings, bool commit) {
      // Prase settings string
      settings = settings.substring(0, settings.length() - 2);

      // Assign new values
      RobotName = getValue(settings, ',', 0);
      leftForwardSpeed = getValue(settings, ',', 1).toInt();
      rightForwardSpeed = getValue(settings, ',', 2).toInt();
      leftBackwardSpeed = getValue(settings, ',', 3).toInt();
      rightBackwardSpeed = getValue(settings, ',', 4).toInt();
      robotColor = getValue(settings, ',', 5).toInt();
      
      // Save values to EEPROM
      if (commit)
      {
        EEPROM.writeString(0, RobotName);
        EEPROM.writeInt(100, leftForwardSpeed);
        EEPROM.writeInt(104, rightForwardSpeed);
        EEPROM.writeInt(108, leftBackwardSpeed);
        EEPROM.writeInt(112, rightBackwardSpeed);
        EEPROM.writeInt(116, robotColor);
        EEPROM.commit();
      }
    }

    /*
     * Called when the robot neesd to load its settings.
     * Should return a JSON object of all the modifiable movement parameters.
     */
    String loadSettings(){
      String content = "{\"name\": \"";
      content += RobotName;
      content += "\", \"controls\": [{ \"name\": \"leftForwardSpeed\", \"displayname\": \"Left Forward Speed\", \"min\": 50, \"max\": 150, \"increment\": 1, \"current\":";
      content += String(leftForwardSpeed);
      content += "},{ \"name\": \"rightForwardSpeed\", \"displayname\": \"Right Forward Speed\", \"min\": 50, \"max\": 150, \"increment\": 1, \"current\":";
      content += String(rightForwardSpeed);
      content += "},{ \"name\": \"leftBackwardSpeed\", \"displayname\": \"LEft backward Speed\", \"min\": 50, \"max\": 150, \"increment\": 1, \"current\":";
      content += String(leftBackwardSpeed);
      content += "},{ \"name\": \"rightBackwardSpeed\", \"displayname\": \"Right Backward Speed\", \"min\": 50, \"max\": 150, \"increment\": 1, \"current\":";
      content += String(rightBackwardSpeed);
      content += "},{ \"name\": \"robotColor\", \"displayname\": \"Color\", \"min\": 0, \"max\": 6, \"increment\": 1, \"current\":";
      content += String(robotColor);
      content +="}]}";
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
      showImage(images::Happy, (colors)robotColor);
      return;
    }

  private:
    CRGBArray<25> leds;
    // Temperature sensor not currently used
    //Generic_LM75 Tmp75Sensor;
    MPU6050 mpu6050 = MPU6050(Wire);
    int BUZZER_PIN = 33;
    int BUZZER_CHANNEL = 0;

    // Image maps for display
    uint8_t image_maps[14][5] = {
      {B00000,B00000,B00000,B00000,B00000}, // Clear
      {B00100,B01100,B00100,B00100,B01110}, // 1
      {B11100,B00010,B01100,B10000,B11110}, // 2
      {B11110,B00010,B00100,B10010,B01100}, // 3
      {B00110,B01010,B10010,B11111,B00010}, // 4
      {B11111,B10000,B11110,B00001,B11110}, // 5
      {B00010,B00100,B01110,B10001,B01110}, // 6
      {B11111,B00010,B00100,B01000,B10000}, // 7
      {B01110,B10001,B01110,B10001,B01110}, // 8
      {B01110,B10001,B01110,B00100,B01000}, // 9
      {B01010,B01010,B00000,B10001,B01110}, // Happy
      {B01010,B01010,B00000,B01110,B10001}, // Sad
      {B01010,B00000,B00100,B01010,B00100}, // Surprised
      {B01100,B11100,B01111,B01110,B00000}  // Duck
    };

    // Color maps for display
    CRGB color_map[7] = {
      CRGB(255, 0, 0),
      CRGB(0, 255, 0),
      CRGB(0, 0, 255),
      CRGB(255, 128, 0),
      CRGB(255, 0, 196),
      CRGB(255, 96, 0),
      CRGB(144, 144, 128)
    };
   
    // Returns string at index of another string separated by deliminator
    String getValue(String data, char separator, int index){
      int found = 0;
      int strIndex[] = {0, -1};
      int maxIndex = data.length()-1;

      for(int i=0; i <= maxIndex && found <= index; i++){
        if(data.charAt(i) == separator || i == maxIndex){
            found++;
            strIndex[0] = strIndex[1]+1;
            strIndex[1] = (i == maxIndex) ? i+1 : i;
        }
      }
      return found > index ? data.substring(strIndex[0], strIndex[1]) : "";
    }

    // Displays an image on the LED screen
    void Display(uint8_t dat[], CRGB myRGBcolor){
      for (int c = 0; c < 5; c++)
      {
        for (int r = 0; r < 5; r++)
        {
          if (bitRead(dat[c], r))
          {
            leds[c * 5 + 4-r] = myRGBcolor;
          }
          FastLED.show();
          delay(5);
        }
      }
    }
};

// Defines the WiFi class
class WiFiCommunication {
  private:
    String ssid, pass;
    IPAddress serverIP;
    int port;
    Robot* bot;
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
              bot->turn(1, magnitude);
              break;
            case 1:
              // Right
              bot->turn(0, magnitude);
              break;
            case 2:
              // Forward
              bot->driveForward(magnitude);
              break;
            case 3:
              // Backup
              bot->driveBackward(magnitude);
              break;
          }
        }
        else
        {
          // Robot trying to move, but is blocked
          bot->blockedMove();
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
            bot->takeDamage(magnitude);
            break;
        }
        delay(1000);
      }
      // Forces a response to the server, resets the WiFi on fail
      String response = "ERROR";
      do
      {
        // This should really be a POST request, but GET is more reliable
        String message = "GET /Bot/Done?bot=";
        message = message + bot->botNum + " HTTP/1.1\r\nHost: " + serverIP.toString() + ":" + String(port) + "\r\nConnection: close\r\n\r\n";
        // Notify server that bot has finished moving, check for acknowledgment
        response = sendCommand(message, F("AK\n"));     
      } while (response.indexOf(F("ERROR")) != -1);
    }

    // Receives and prcesses commands while in setup mode
    void setupMode(String Message) {
      // Prase instruction
      int instruction = Message.substring(0, Message.indexOf(':')).toInt();

      // Check if a response is needed here
      if (instruction != 0) {
        // Respond and close the connection
        client.print(F("OK"));


        // Parse the message
        Message = Message.substring(Message.indexOf(':') + 1);
      }

      if (instruction == 0) 
      {
        // Load the settings
        String settings = bot->loadSettings();
        // Send the settings to the game server
        client.println(settings);
      }
      else if (instruction == 1) 
      {
        // Save the settings temporarily
        bot->saveSettings(Message, false);
        // Run a speed test
        bot->speedTest();
      }
      else if (instruction == 2) 
      {
        // Save the settings temporarily
        bot->saveSettings(Message, false);
        // Run a navigation test
        bot->navigationTest();
      }
      else if (instruction == 3) 
      {
        // Save the settings persistently and exit setup mode
        bot->saveSettings(Message, true);
        inSetupMode = false;
        bot->showImage(Robot::images::Happy, (Robot::colors)bot->robotColor);
      }     
    }
    
  public:
    bool inSetupMode = false;
    WiFiServer server = WiFiServer(8080);
    WiFiClient client;

    WiFiCommunication(){}
    
    void begin(IPAddress ServerIP, int ServerPort, String SSID, String WPA_Pass, Robot* Bot)
    {
      Serial.println("Starting WiFi");
      serverIP = ServerIP;
      port = ServerPort;
      ssid = SSID;
      pass = WPA_Pass;
      bot = Bot;
    }

    // Sets up the robot, connecting to the Wi-Fi, informing the server of itself, and so on.
    bool Startup() {
          // Set WiFi to station mode and disconnect from an AP if it was previously connected
          WiFi.mode(WIFI_STA);
          WiFi.disconnect();
          delay(100);
          
          // Connect to AP
          WiFi.begin(ssid.c_str(), pass.c_str());

          // Ensure connection
          int i = 0;
          while (WiFi.status() != WL_CONNECTED && i < 5) {
            delay(500);
            i++;
          }
          if (WiFi.status() != WL_CONNECTED){
            return false;
          }

          // Get asigned IP
          String client = WiFi.localIP().toString(); 

          // Start server
          server.begin();
        
          // Inform server of bot
          String message = "GET /Bot/Index?ip=";
          message = message + client + "&name=" + bot->RobotName + " HTTP/1.1\r\nHost: " + serverIP.toString() + ":" + String(port) + "\r\nConnection: close\r\n\r\n"; 
          String response = sendCommand(message, F("AK\n"));
          if (response.indexOf(F("ERROR")) != -1)
          {
            return false;
          }        
          return true;
        }

        // Processes a message from the game server
        void MessageReceived (String message) {
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
              bot->reset();
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
              bot->playerAssigned(message[0] - '0');
              // Get assigned bot number
              bot->botNum = message.substring(1, message.indexOf('\n'));
              started = true;
            }
            else if (instruction == 1)
            {
              // Enter setup mode
              inSetupMode = true;
              bot->showImage(Robot::images::Duck, (Robot::colors)bot->robotColor);
            }
          }
      }

      /* Send message through WiFi module
      * message is the message to send (blank for read data back)
      * EoT is the End of Tranmission string that indicates
      * to stop reading. ERROR will always terminate.
      * If EoT is an empty string, the message will be sent
      * but the method won't wait for a response.
      * The method will timeout after ~8 seconds of not finding EoT or ERROR
      */
      String sendCommand(String message, String EoT) {
        String response = "";
        if (message != "")
        {
          if (client.connect(serverIP, port))
          {
            client.print(message);
            delay(5);
          }
          else 
          {
            return "ERROR";  
          }
        }
        // Check if reading from module
        if (EoT != F(""))
        {
          int i = 0;
          // Read until the end EoT string is found, or timeout
          while (response.indexOf(F("ERROR")) == -1 && response.indexOf(EoT) == -1 && i < 8000)
          {
            while (client.available())
            {
              // Read from module
              response += (char)client.read();
            }
            i++;
            delay(1);
          }
          client.stop();
          if (i == 8000)
          {
            // Timed out
            return F("ERROR");
          }
      }
      return response;
    }
};

String SSID = "RoboRuckus";
String WPA_Pass = "Password";
IPAddress IP(192, 168, 3, 1);
int Port = 8082;
// Create the robot object
Robot bot;
// Create wifi object
WiFiCommunication wifi;

void setup() {
  // Start the serial connection
  Serial.println("Start");
  Serial.begin(115200);
  Wire.begin(22,21);

  //Initialize robot
  bot.begin();
  //Initialize the WiFi module and connect to server
  wifi.begin(IP, Port, SSID, WPA_Pass, &bot);
  while (!wifi.Startup()) {
    bot.showImage(Robot::images::Sad, (Robot::colors)bot.robotColor);
    delay(1000);
  }
  bot.showImage(Robot::images::Happy, (Robot::colors)bot.robotColor);
}

void loop() {
  wifi.client = wifi.server.available();
  if (wifi.client) // Check if the WiFi server has a message
  {
    if (wifi.client.connected()) 
    {
      // Read message, should be terminated by \n (new line) character
      String message = "";
      while (wifi.client.available())
      {
        // Read from module
        message += (char)wifi.client.read();
        delay(5);
      }
      // Check if in setup mode
      if (!wifi.inSetupMode){
        // Respond
        wifi.client.print(F("OK"));
      }
      // Pass message to WiFi object for processing
      wifi.MessageReceived(message);
      // Close the connection
      wifi.client.stop();
    }
  }
}
