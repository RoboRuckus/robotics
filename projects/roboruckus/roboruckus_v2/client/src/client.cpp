// This is Josh's WIP pseudocode
// Being built from:
// tagnw/robotics:projects/roboruckus/arduino_ruckus_mm/Mbits/Ringbit Car/Ringbit_Car_PlatformIO/src/main.cpp

/*
Robo Hardware should be in Robot Class
WiFi class for communication
Game client class for logic interpretation
Load settings function for SPIFFs / filesystem stuff
*/

///////////
// SETUP //
///////////

void setup() {
  hardwareInit();
  communicationInit();
  gameClientInit();
}

void hardwareInit() {
  logger.begin();
  robot.begin();
}

void communicationInit() {
  wifi_communication.begin();
}

void gameClientInit() {
  game_client.begin();
}

//////////
// LOOP //
//////////

void loop() {
  checkForReboot()
  checkForCalibrationRequest()
  checkForServerMessage()
}
