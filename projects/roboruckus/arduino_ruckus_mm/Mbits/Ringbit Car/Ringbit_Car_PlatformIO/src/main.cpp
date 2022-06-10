/*
 * This file is licensed under the MIT Lesser General Public License Copyright (c) 2022 Technology Alliance Group NW (https://tagnw.org)
 *
 * Template for RoboRuckus game robot based on the 
 * ESP32 based Mbits board via Arduino platform.
 * https://www.elecrow.com/mbits.html
 *
 * This code is intended to work with the Ring:but Car v2
 * https://www.elecfreaks.com/ring-bit-car-v2-for-micro-bit.html
 * 
 * External libraries needed:
 * FastLED https://github.com/FastLED/FastLED
 * Temperature_LM75_Derived: https://github.com/jeremycole/Temperature_LM75_Derived <-- Not currently used
 * Tone32: https://github.com/lbernstone/Tone32 <-- Not currently used
 * MPU6050_tockn: https://github.com/Tockn/MPU6050_tockn
 * AsyncTCP: https://github.com/esphome/AsyncTCP
 * ESPAsyncWebServer: https://github.com/esphome/ESPAsyncWebServer
 * ESPAsyncWiFiManager: https://github.com/alanswx/ESPAsyncWiFiManager
 * ArduinoJson: https://github.com/bblanchon/ArduinoJson
 *
 * Contributors: Sam Groveman
 */

#include <Arduino.h>
#include <Update.h>
#include <FS.h>
#include <ArduinoJson.h>
#include <ESPAsyncWebServer.h>
#include <ESPAsyncWiFiManager.h>
#include <SPIFFS.h>
#include <Wire.h>
#include <FastLED.h>
#include <MPU6050_tockn.h>
#include <ESP32Servo.h>
#include <ESPmDNS.h>

// Global function declarations (there's probably a better way to handle this)
void updateServerStart();
void updateServerStop();
void onUpdate(AsyncWebServerRequest *request, String filename, size_t index, uint8_t *data, size_t len, bool final);

// Defines the robot class
class Robot {
  #define FRONT_LEDS_PIN  26
  #define NUM_FRONT_LEDS  2
  #define RIGHT_SERVO_PIN 25
  #define LEFT_SERVO_PIN  32
  
  public:
    // Robot variables
    int playerNumber = 0;
    String RobotName, botNum;
    int robotColor = 0;
    
    // If robot supports lateral movement change to "true", else "false"
    String lateral = "false";

  
    // Enums for display colors and images
    enum class colors { Red, Green, Blue, Yellow, Purple, Orange, Cyan, White };
    enum class images { Clear, One, Two, Three, Four, Five, Six, Seven, Eight, Nine, Happy, Sad, Surprised, Duck, Check };
    images currentImage = images::Clear;
    
    // Initialize robot
    Robot(){}
    // Actually initialize robot with call to begin method
    void begin() {
      Serial.println("Initializing robot");
      // Start LEDs
      FastLED.addLeds<WS2812B, 13, GRB>(leds, 25);
      FastLED.addLeds<WS2812B, FRONT_LEDS_PIN, GRB>(frontLED, NUM_FRONT_LEDS);
      FastLED.setBrightness(10);
      FastLED.clear();
      delay(50);
      FastLED.show();

      // Start IMU
      mpu6050.begin();
      calibrateGyro();

      // Start servos
      // Allow allocation of all timers
      ESP32PWM::allocateTimer(0);
      ESP32PWM::allocateTimer(1);
      ESP32PWM::allocateTimer(2);
      ESP32PWM::allocateTimer(3);
      // Attach servos
      left.setPeriodHertz(50);  // Standard 50hz servo
      right.setPeriodHertz(50); 
      left.attach(LEFT_SERVO_PIN, 500, 2500); // pin, min pulse, max pulse
      right.attach(RIGHT_SERVO_PIN, 500, 2500);

      // Set default settings values
      RobotName = "Test%20Bot";
      leftForwardSpeed = 165;
      rightForwardSpeed = 15;
      leftBackwardSpeed = 15;
      rightBackwardSpeed = 165;
      linearTime = 1200;
      drift = 5;
      driftBoost = 10;
      turnAngle = 90;
      robotColor = 0;

      // Attempt to load saved values
      if (SPIFFS.begin()) {
        Serial.println("Mounted file system");
        if (SPIFFS.exists("/robot_config.txt")) 
        {
          // File exists, reading and loading
          Serial.println("Reading robot config file");
          File configFile = SPIFFS.open("/robot_config.txt", "r");
          if (configFile) 
          {
            Serial.println("Opened robot config file, loading settings");
            String settings = "";
            // Read file
            while(configFile.available())
            {
              settings += configFile.readString();
            }
            configFile.close();
            Serial.println("Settings loaded: " + settings);
            // Apply loaded settings
            saveSettings(settings, false);            
          } 
          else 
          {
            Serial.println("Robot config file could not be opened");
          }
        }
        else 
        {
          Serial.println("Robot config file not found");
        }
      } 
      else 
      {
        Serial.println("Failed to mount FS");
        // Clean FS
        Serial.println("Formatting SPIFFS, this will take a while, please wait...");
        SPIFFS.format();
        Serial.println("Done, rebooting");
        ESP.restart();
      }
    }
    
    // Called when a player is assigned to the robot
    void playerAssigned(int player) {
      showImage((images)player, (colors)robotColor);
      playerNumber = player;
    }

    // Display an image in a color on the screen
    void showImage(images image, colors color, bool cache = true) {
      // Save current image
      if (cache && currentImage != image)
      { 
        currentImage = image;
      }
      FastLED.clear();
      delay(10);
      Display(image_maps[(int)image], color_map[(int)color]);
      showColor(color_map[(int)color]);
    }

    /* 
     *  Called when the robot needs to turn.
     *  direction: 0 = right, 1 = left.
     */
    void turn(int direction, int magnitude) {
      // Calculate total turn degrees
      int target = (turnAngle * magnitude) - 10; // The -10 seems to be a hack for the sensor to get accurate turns
      // Create a smart pointer to a new GyroHelper object. Smart pointer aids in deallocation
      std::unique_ptr<GyroHelper> helper(new GyroHelper(mpu6050));
      // Check direction of turn and activate motors appropriately.
      if (direction == 0)
      {
        left.write(leftForwardSpeed);
        right.write(rightBackwardSpeed);
      }
      else if (direction == 1)
      {
        left.write(leftBackwardSpeed);
        right.write(rightForwardSpeed);
      }
      else
      {
        // Bad command, exit.
        return;
      }
      // Keep turning until target angle is met
      while (abs(helper->getAngle()) < target)
      {
        delay(20);
      }
      // Stop motors      
      left.write(90);
      right.write(90);
    }

    // Called when the robot needs to drive forward
    void driveForward(int magnitude) {
      // Calculate total time needed for the move
      int total = linearTime * magnitude;
      float gyroX;
      // Create a smart pointer to a new GyroHelper object. Smart pointer aids in deallocation
      std::unique_ptr<GyroHelper> helper(new GyroHelper(mpu6050));
      int leftSpeed;
      int rightSpeed;
      long start = millis();
      // Keep driving until time limit is reached
      while (millis() - start < total) 
      {
        gyroX = helper->getAngle();
        /*
         * Check if the robot has drifted of course using the gyro.
         * If it has, then increase the speed of one wheel until the
         * robot is back on course.
         */
        if (gyroX > drift)
        {
          rightSpeed = rightForwardSpeed - driftBoost;
          leftSpeed = leftForwardSpeed;
        }
        else if (gyroX < -drift) 
        {
          rightSpeed = rightForwardSpeed;
          leftSpeed = leftForwardSpeed + driftBoost;
        }
        else 
        {
          rightSpeed = rightForwardSpeed;
          leftSpeed = leftForwardSpeed;
        }
        // Set the motors to the appropriate speed
        left.write(leftSpeed);
        right.write(rightSpeed);
        delay(50);
      }
      // Stop motors
      left.write(90);
      right.write(90); 
    }

    // Called when the robot needs to drive backward
    void driveBackward(int magnitude) {
       // Calculate total time needed for the move
      int total = linearTime * magnitude;
      float gyroX;
      // Create a smart pointer to a new GyroHelper object. Smart pointer aids in deallocation
      std::unique_ptr<GyroHelper> helper(new GyroHelper(mpu6050));
      int leftSpeed;
      int rightSpeed;
      long start = millis();
      // Keep driving until time limit is reached
      while (millis() - start < total) {
        gyroX = helper->getAngle();
        /*
         * Check if the robot has drifted of course using the gyro.
         * If it has, then increase the speed of one wheel until the
         * robot is back on course.
         */
        if (gyroX > drift) {
          rightSpeed = rightBackwardSpeed;
          leftSpeed = leftBackwardSpeed - driftBoost;
        }
        else if (gyroX < (0 - drift)) {
          rightSpeed = rightBackwardSpeed + driftBoost;
          leftSpeed = leftBackwardSpeed;
        }
        else 
        {
          rightSpeed = rightBackwardSpeed;
          leftSpeed = leftBackwardSpeed;
        }
        // Set the motors to the appropriate speed
        left.write(leftSpeed);
        right.write(rightSpeed);
        delay(50);
      }
      // Stop the motors
      left.write(90);
      right.write(90);
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
     * commit: true when the settings should be saved to persistent storage like EEPROM.
     * Should also update robot movement parameter variables with new values.
     */
    void saveSettings(String settings, bool commit) {
      // Prase settings string
      String settings_clean = settings.substring(0, settings.length() - 2);

      /* 
       * Assign new values.
       * The motor speed is set via the Servo library, which uses a value between 0-180.
       * At the middle value, 90, the motors don't turn, above that value the motors
       * turn one direction increasing in speed the further from 90. Below 90 is the same
       * only the wheels turn the opposite direction. To let the user set a value from 0-90
       * with 90 being the fastest, you need to subtract each value from 90 when receiving 
       * or sending the value if the desired setting is below 90. For wheels that need to
       * have values above 90, 90 must be added.
       */
      RobotName = getValue(settings_clean, ',', 0);
      leftForwardSpeed = getValue(settings_clean, ',', 1).toInt() + 90;
      rightForwardSpeed = 90 - getValue(settings_clean, ',', 2).toInt();
      leftBackwardSpeed = 90 - getValue(settings_clean, ',', 3).toInt();
      rightBackwardSpeed = getValue(settings_clean, ',', 4).toInt() + 90;
      linearTime = getValue(settings_clean, ',', 5).toInt();
      drift = getValue(settings_clean, ',', 6).toInt();
      driftBoost = getValue(settings_clean, ',', 7).toInt();
      turnAngle = getValue(settings_clean, ',', 8).toFloat();
      robotColor = getValue(settings_clean, ',', 9).toInt();
      
      // Save values to file
      if (commit)
      {
        Serial.println("Saving config");
        File configFile = SPIFFS.open("/robot_config.txt", "w");
        if (!configFile) {
          Serial.println("Failed to open config file for writing");
        }
        else
        {
          configFile.print(settings);
          configFile.close();     
        }
      }
    }

    /*
     * Called when the robot needs to load its settings.
     * Should return a JSON object of all the modifiable movement parameters.
     */
    String loadSettings() {
      String content = "{\"name\": \"";
      content += RobotName;
      content += "\", \"controls\": [{ \"name\": \"leftForwardSpeed\", \"displayname\": \"Left Forward Speed\", \"min\": 0, \"max\": 90, \"increment\": 1, \"current\":";
      content += String(leftForwardSpeed - 90);
      content += "},{ \"name\": \"rightForwardSpeed\", \"displayname\": \"Right Forward Speed\", \"min\": 0, \"max\": 90, \"increment\": 1, \"current\":";
      content += String(90 - rightForwardSpeed);
      content += "},{ \"name\": \"leftBackwardSpeed\", \"displayname\": \"Left Backward Speed\", \"min\": 0, \"max\": 90, \"increment\": 1, \"current\":";
      content += String(90 - leftBackwardSpeed);
      content += "},{ \"name\": \"rightBackwardSpeed\", \"displayname\": \"Right Backward Speed\", \"min\": 0, \"max\": 90, \"increment\": 1, \"current\":";
      content += String(rightBackwardSpeed - 90);
      content += "},{ \"name\": \"linearTime\", \"displayname\": \"Linear Movement Time\", \"min\": 500, \"max\": 2000, \"increment\": 10, \"current\":";
      content += String(linearTime);
      content += "},{ \"name\": \"drift\", \"displayname\": \"Drift Limit\", \"min\": 0, \"max\": 15, \"increment\": 1, \"current\":";
      content += String(drift);
      content += "},{ \"name\": \"driftBoost\", \"displayname\": \"Drift Boost\", \"min\": 0, \"max\": 20, \"increment\": 1, \"current\":";
      content += String(driftBoost);
      content += "},{ \"name\": \"turnAngle\", \"displayname\": \"Turn Angle\", \"min\": 60, \"max\": 120, \"increment\": 0.5, \"current\":";
      content += String(turnAngle);
      content += "},{ \"name\": \"robotColor\", \"displayname\": \"Color\", \"min\": 0, \"max\": 7, \"increment\": 1, \"current\":";
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
      turn(0, 1);
      delay(1000);
      turn(1, 1);
      delay(1000);
      turn(0, 2);
    }

    // Called when the game is reset
    void reset() {
      playerNumber = 0;
      showImage(images::Happy, (colors)robotColor);
      return;
    }

    // Calibrates the gyroscope offsets
    void calibrateGyro() {
      mpu6050.calcGyroOffsets(true, 2000, 1000);
      Serial.println("");
    } 

  private:
    CRGBArray<25> leds;
    CRGBArray<NUM_FRONT_LEDS> frontLED;
    // Temperature sensor not currently used
    // Generic_LM75 Tmp75Sensor;
    MPU6050 mpu6050 = MPU6050(Wire);
    // Buzzer not currently used
    // int BUZZER_PIN = 33;
    // int BUZZER_CHANNEL = 0;
    Servo left, right;

    // Robot movement parameters 
    int leftForwardSpeed, rightForwardSpeed, rightBackwardSpeed, leftBackwardSpeed, linearTime, driftBoost, drift;
    float turnAngle;

    // Image maps for display. Binary maps for each row, 1 on, 0 off.
    uint8_t image_maps[15][5] = {
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
      {B01100,B11100,B01111,B01110,B00000}, // Duck
      {B00000,B00001,B00010,B10100,B01000}  // Check
    };

    // Color maps for display
    CRGB color_map[8] = {
      CRGB(255, 0, 0),    // Red
      CRGB(0, 255, 0),    // Green
      CRGB(0, 0, 255),    // Blue
      CRGB(255, 128, 0),  // Yellow
      CRGB(255, 0, 196),  // Purple
      CRGB(255, 96, 0),   // Orange
      CRGB(0, 196, 255),  // Cyan
      CRGB(144, 144, 128) // White
    };
    
    // Takes a string and splits it by a deliminator and returns substring at desired index
    String getValue(String data, char separator, int index) {
      int found = 0;
      // Create array to hold indices that bound the substring found between delimiters
      int strIndex[] = {0, -1};
      int maxIndex = data.length()-1;

      // Look for substring between delimiters
      for(int i=0; i <= maxIndex && found <= index; i++) {
        if(data.charAt(i) == separator || i == maxIndex) 
        {
            found++;
            strIndex[0] = strIndex[1] + 1;
            strIndex[1] = (i == maxIndex) ? i + 1 : i;
        }
      }
      // If a substring was found at the desired index return it, else return an empty string
      return found > index ? data.substring(strIndex[0], strIndex[1]) : "";
    }

    // Displays an image on the LED screen
    // Adapted from https://www.elecrow.com/wiki/index.php?title=Mbits#Use_with_Mbits-RGB_Matrix
    void Display(uint8_t dat[], CRGB myRGBcolor) {
      for (int c = 0; c < 5; c++)
      {
        for (int r = 0; r < 5; r++)
        {
          if (bitRead(dat[c], r))
          {
            // Set the LED color at the given column and row
            leds[c * 5 + 4-r] = myRGBcolor;
          }
        }
      }
      FastLED.show();
    }

    // Show color on front LEDs
    void showColor(CRGB myRGBcolor) {
      for (int i = 0; i < frontLED.len; i++)
      {
        frontLED[i] = myRGBcolor;
      }
      FastLED.show();
    }

    /*
     * Helper class for getting angle robot has turned.
     * Used because the MPU6050 library gyroAngle can't
     * be reset without calling begin() method again.
     */
    class GyroHelper {
      public:
        // Initialize the helper using a the specific sensor
        GyroHelper(MPU6050 &Gyro) : gyro(Gyro) {
          previousTime = millis();  
          gyro.update();        
        }

        // Get the angle turned since last called
        float getAngle() {
          gyro.update();
          // Get rotation in deg/s
          float gyroX = gyro.getGyroX();
          // Calculate time since last call in seconds
          interval = (millis() - previousTime) * 0.001;
          previousTime = millis();
          // Calculate total degrees turned so far
          totalAngle += gyroX * interval;
          // Return total angle turned
          return totalAngle;
        }

      private:
        MPU6050 &gyro;
        long previousTime;
        float interval = 0;
        float totalAngle = 0;
    };
};

// Defines the WiFi class
class WiFiCommunication {
  private:
    IPAddress serverIP;
    int port;
    Robot* bot;
    bool started = false;
    
    // Executes a move received by the bot
    void executeMove(uint8_t movement, uint8_t magnitude, uint8_t lateralMove) {
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
        }
      }
      // Non-movement command
      else 
      {
        switch(movement)
        {
          case 4:
            // Take damage
            bot->takeDamage(magnitude);
            break;
        }
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

    // Receives and processes commands while in setup mode
    void setupMode(String Message) {
      // Prase instruction
      int instruction = Message.substring(0, Message.indexOf(':')).toInt();

      // Check if a response is needed here
      if (instruction != 0)
      {
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
        bot->showImage(Robot::images::Duck, (Robot::colors)bot->robotColor);
        // Run a speed test
        bot->speedTest();
      }
      else if (instruction == 2) 
      {
        // Save the settings temporarily
        bot->saveSettings(Message, false);
        bot->showImage(Robot::images::Duck, (Robot::colors)bot->robotColor);
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
    WiFiServer botserver = WiFiServer(8080);
    WiFiClient client;

    // Initialize WiFi object
    WiFiCommunication(){}
    // Setup WiFi object with all necessary info
    void begin(IPAddress ServerIP, int ServerPort, Robot* Bot) {
      Serial.println("Starting WiFi");
      serverIP = ServerIP;
      port = ServerPort;
      bot = Bot;
    }

    // Sets up the robot, connecting to the Wi-Fi, informing the server of itself, and so on.
    bool Startup() {
      // Get assigned IP
      String ip = WiFi.localIP().toString();

      // Start server
      botserver.begin();
    
      // Inform server of bot
      String message = "GET /Bot/Index?ip=";
      message = message + ip + "&name=" + bot->RobotName + "&lateralMovement=" + bot->lateral + " HTTP/1.1\r\nHost: " + serverIP.toString() + ":" + String(port) + "\r\nConnection: close\r\n\r\n"; 
      String response = sendCommand(message, F("AK\n"));
      if (response.indexOf(F("ERROR")) != -1)
      {
        return false;
      }        
      return true;
    }

    // Processes a message from the game server
    void MessageReceived (String message) {
      // Check if in setup mode
      if (!inSetupMode)
      {
        // Respond
        client.print(F("OK"));
      }		  
      // Check if game is already started
      if (started) 
      {
        // Parse movement instruction
        uint8_t movement = message[0] - '0';   // Convert char to int
        uint8_t magnitude = message[1] - '0';  // Convert char to int
        uint8_t lateralMove = message[2] - '0';  // Convert char to int
        if (lateralMove == 2)
        {
          // Bot received reset command
          started = false;
          // Restart the update server
          updateServerStart();
          bot->reset();
        }
        else
        {
          // Bot received move order
          executeMove(movement, magnitude, lateralMove);
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
          // Stop the update server while robot is in the game and ready to play
          updateServerStop();
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

/* Global variables */

// Text of update webpage
String indexPage = "<!DOCTYPE html>\
<html lang='en-us'>\
<head>\
<title>Firmware Updater</title>\
</head>\
<body>\
<div id='up-wrap'>\
  <h2>Upload Firmware</h2>\
  <div id='up-progress'>\
    <div id='up-bar'></div>\
    <div id='up-percent'>0%</div>\
  </div>\
  <input type='file' id='up-file' disabled />\
  <label for='up-file' id='up-label'>\
    Update\
  </label>\
  <div id='message'></div>\
</div>\
<script>\
 var uprog = {\
	hBar : null,\
	hPercent : null,\
	hFile : null,\
	init : () => {\
		uprog.hBar = document.getElementById('up-bar');\
		uprog.hPercent = document.getElementById('up-percent');\
		uprog.hFile = document.getElementById('up-file');\
		uprog.hFile.disabled = false;\
		document.getElementById('up-label').onclick = uprog.upload;\
	},\
	update : (percent) => {\
	  percent = percent + '%';\
	  uprog.hBar.style.width = percent;\
	  uprog.hPercent.innerHTML = percent;\
	  if (percent == '100%') { uprog.hFile.disabled = false; }\
	},\
	upload : () => {\
    if(uprog.hFile.files.length == 0 ){\
      return;\
    }\
	  let file = uprog.hFile.files[0];\
	  uprog.hFile.disabled = true;\
	  uprog.hFile.value = '';\
    let xhr = new XMLHttpRequest(), data = new FormData();\
	  data.append('upfile', file);\
	  xhr.open('POST', '/update');\
	  let percent = 0, width = 0;\
	  xhr.upload.onloadstart = (evt) => { uprog.update(0); };\
	  xhr.upload.onloadend = (evt) => { uprog.update(100); };\
	  xhr.upload.onprogress = (evt) => {\
		percent = Math.ceil((evt.loaded / evt.total) * 100);\
		uprog.update(percent);\
	  };\
	  xhr.onload = function () {\
		if (this.response!='OK' || this.status!=200) {\
		  document.getElementById('message').innerHTML = 'ERROR!';\
		} else {\
		  uprog.update(100);\
		  document.getElementById('message').innerHTML = 'Success, rebooting!';\
		}\
	  };\
	  xhr.send(data);\
	}\
};\
window.addEventListener('load', uprog.init);\
</script>\
<style>\
#message{font-size:18px;font-weight:bolder}\
#up-file,#up-label{width:100%;height:44px;border-radius:4px;margin:10px auto;font-size:17px}\
#up-label{background:#f1f1f1;border:0;display:block;line-height:44px}\
body{background:#3498db;font-family:sans-serif;font-size:14px;color:#777}\
#up-file{padding:0;border:1px solid #ddd;line-height:44px;text-align:left;display:block;cursor:pointer}\
#up-bar,#up-progress{background-color:#f1f1f1;border-radius:10px;position:relative}\
#up-bar{background-color:#3498db;width:0%;height:30px}\
#up-wrap{background:#fff;max-width:258px;margin:75px auto;padding:30px;border-radius:5px;text-align:center}\
#up-label{background:#3498db;color:#fff;cursor:pointer}\
#up-percent{position:absolute;top:6px;left:0;width:100%;display:flex;align-items:center;justify-content:center;text-shadow:-1px 1px 0 #000,1px 1px 0 #000,1px -1px 0 #000,-1px -1px 0 #000;color:#fff}</style>\
</body>\
</html>";

// For dynamic game server settings
char game_server[40] = "192.168.3.1";
char game_port[6] = "8082";

// Reboot on firmware update flag
bool shouldReboot = false;

// Pin with button to reset WiFi settings (hold for ~5 seconds on boot to reset)
const int RESET_PIN = 36;

// Push button anytime after connecting to game server to calibrate gyro
const int CALIBRATE_PIN = 36;

// Create the robot object
Robot bot;
// Create wifi object
WiFiCommunication wifi;
// Flag for saving data
bool shouldSaveConfig = false;
// Create webserver object
AsyncWebServer server(80);

/* Global functions */

// Starts the update server
void updateServerStart() {
  Serial.println("Starting update server");
  MDNS.begin("Web-Update.local");
  // Add requests
  server.on("/", HTTP_GET, [](AsyncWebServerRequest *request) {
    request->send(200, "text/html", indexPage);
  });

  // Upload a file
  server.on("/update", HTTP_POST, [](AsyncWebServerRequest *request) {
    shouldReboot = !Update.hasError();
    AsyncWebServerResponse *response = request->beginResponse(200, "text/plain", shouldReboot?"OK":"FAIL");
    response->addHeader("Connection", "close");
    request->send(response);
  }, onUpdate);

  server.onNotFound([](AsyncWebServerRequest *request) {
    request->send(404);
  });

  server.begin();
  MDNS.addService("http", "tcp", 80);
}

// Stops the update server
void updateServerStop() {
  Serial.println("Stopping update server");
  server.reset();
  server.end();
  MDNS.end();
}

// Handle firmware update
void onUpdate(AsyncWebServerRequest *request, String filename, size_t index, uint8_t *data, size_t len, bool final){
  if(!index)
  {
    Serial.printf("Update Start: %s\n", filename.c_str());
    // Ensure firmware will fit into flash space
    if(!Update.begin((ESP.getFreeSketchSpace() - 0x1000) & 0xFFFFF000))
    {
      Update.printError(Serial);
    }
  }
  if(!Update.hasError())
  {
    if(Update.write(data, len) != len)
    {
      Update.printError(Serial);
    }
  }
  if(final)
  {
    if(Update.end(true))
    {
      Serial.printf("Update Success: %uB\n", index+len);
    } 
    else
    {
      Update.printError(Serial);
    }
  }
}

// Callback notifying us of the need to save config
void saveConfigCallback() {
  Serial.println("Should save config");
  shouldSaveConfig = true;
}

// Callback notifying that the access point has started
void configModeCallback(AsyncWiFiManager *myWiFiManager){
  Serial.println("Access point started");
  bot.showImage(Robot::images::Duck, (Robot::colors)bot.robotColor);
}

void setup() {
  pinMode(RESET_PIN, INPUT_PULLUP);

  // Local initialization. Once its business is done, there is no need to keep it around
  DNSServer dns;
  AsyncWiFiManager wifiManager(&server,&dns);

  // Start the serial connection
  Serial.begin(115200);
  Serial.println("Starting");
  Wire.begin(22,21);

  // Initialize robot
  bot.begin();

  // Check for reset
  if (digitalRead(RESET_PIN) == LOW)
  {
    Serial.println("Resetting WiFi");
    wifiManager.resetSettings();
    bot.showImage(Robot::images::Check, (Robot::colors)bot.robotColor);
    delay(2000);
    ESP.restart();
  }
 
  // SPIFFS should already be mounted by robot class
  // Load settings and check for WiFi config
  if (SPIFFS.exists("/wifi_config.json"))
  {
    // File exists, reading and loading
    Serial.println("Reading WiFi config file");
    File configFile = SPIFFS.open("/wifi_config.json", "r");
    if (configFile)
    {
      Serial.println("Opened WiFi config file");
      size_t size = configFile.size();
      // Allocate a buffer to store contents of the file.
      char buf[size];
      // Create JSON object to hold data
      StaticJsonDocument<256> json;
      configFile.readBytes(buf, size);
      configFile.close();
      DeserializationError result = deserializeJson(json, buf);
      // Print to serial port what was loaded
      serializeJson(json, Serial);
      if (result.code() == DeserializationError::Ok)
      {
        Serial.println("\nParsed json");
        strcpy(game_server, json["game_server"]);
        strcpy(game_port, json["game_port"]);
      }
      else
      {
        Serial.println("Failed to load WiFi config");
      }
    }
  }
  
  // The extra parameters to be configured (can be either global or just in the setup)
  // After connecting, parameter.getValue() will get you the configured value
  AsyncWiFiManagerParameter custom_game_server("server", "Game Server", game_server, 40);
  AsyncWiFiManagerParameter custom_game_port("port", "Game Port", game_port, 6);

  // Set config save notify callback
  wifiManager.setSaveConfigCallback(saveConfigCallback);

  // Set entered AP mode callback
  wifiManager.setAPCallback(configModeCallback);

  // Add all the parameters here
  wifiManager.addParameter(&custom_game_server);
  wifiManager.addParameter(&custom_game_port);

  // Set SSID to ESP32 chip ID
  String AP_ssid_string = "Ruckus_" + String((uint32_t)ESP.getEfuseMac(), HEX);
  char AP_ssid[AP_ssid_string.length()];
  AP_ssid_string.toCharArray(AP_ssid, AP_ssid_string.length());
  
  // Fetches ssid and password and tries to connect
  // if it does not connect it starts an access point with the specified name
  // and goes into a blocking loop awaiting configuration
  if (!wifiManager.autoConnect(AP_ssid, "RuckusBot"))
  {
    Serial.println("Failed to connect and hit timeout");
    delay(3000);
    //reset and try again, or maybe put it to deep sleep
    ESP.restart();
    delay(5000);
  }
  
  // Read updated parameters
  strcpy(game_server, custom_game_server.getValue());
  strcpy(game_port, custom_game_port.getValue());

  // Save the custom parameters to file
  if (shouldSaveConfig) 
  {
    Serial.println("Saving WiFi config");
    StaticJsonDocument<256> json;
    json["game_server"] = game_server;
    json["game_port"] = game_port;

    File configFile = SPIFFS.open("/wifi_config.json", "w");
    if (!configFile)
    {
      Serial.println("Failed to open WiFi config file for writing");
    }
    else
    {
      serializeJson(json, configFile);
      configFile.close();
    }
  }

  int Port = 8082;
  // Parse game server port and IP address
  // There's probably a better way to do this
  String server_port = String(game_port);
  int server_port_int = server_port.toInt();
  if (server_port_int != 0) 
  {
    Port = server_port_int;
  }

  Serial.println("Parsing saved port and IP");
  byte ip[4];
  if (sscanf(game_server, "%hhu.%hhu.%hhu.%hhu", ip, ip+1, ip+2, ip+3) != 4) 
  {
    Serial.print("Invalid IP: ");
    Serial.println(game_server);
    ip[0] = 192;
    ip[1] = 168;
    ip[2] = 3;
    ip[3] = 1;
  }
  IPAddress IP(ip[0], ip[1], ip[2], ip[3]);
  
  // Clear server settings just in case
  updateServerStop();

  // Start the update server
  updateServerStart();

  // Initialize the WiFi module and connect to server
  wifi.begin(IP, Port, &bot);
  while (!wifi.Startup() && !shouldReboot) 
  {
    bot.showImage(Robot::images::Sad, (Robot::colors)bot.robotColor);
    delay(1000);
  }
  bot.showImage(Robot::images::Happy, (Robot::colors)bot.robotColor);
  Serial.println("Ready!");
}

void loop() {
  // Check for firmware update requiring a reboot
  if (shouldReboot) 
  {
    Serial.println("Firmware updated, rebooting...");
    bot.showImage(Robot::images::Check, (Robot::colors)bot.robotColor);
    // Delay to show image and let server send response
    delay(5000);
    ESP.restart();
  }

  // Check if the calibrate gyro button was pushed
  if (digitalRead(CALIBRATE_PIN) == LOW)
  {
    bot.showImage(Robot::images::Duck, (Robot::colors)bot.robotColor, false);
    bot.calibrateGyro();
    bot.showImage(bot.currentImage, (Robot::colors)bot.robotColor);
  }

  wifi.client = wifi.botserver.available();
  if (wifi.client) // Check if the WiFi server has a message
  {
    if (wifi.client.connected()) 
    {
      // Read message
      String message = "";
      while (wifi.client.available())
      {
        // Read from module
        message += (char)wifi.client.read();
        delay(5);
      }
      // Pass message to WiFi object for processing
      wifi.MessageReceived(message);
      // Close the connection
      wifi.client.stop();
    }
  }
}