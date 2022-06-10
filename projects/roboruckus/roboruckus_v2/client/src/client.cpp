// This is Josh's WIP pseudocode

void setup() {
  hardwareInit()
  checkForWifiInfoReset()
  checkForSavedWifiInformation()

  if(shouldEnterPortal) {
    enterCaptivePortal()
  } else {
    connectToWifi()
  }

  startUpdateServer() // to do the OTA firmware updates
  // TODO: Stop the update server when running the game

  connectToGameServer()
}

void loop() {
  checkForReboot()
  checkForCalibrationRequest()
  checkForServerMessage()
}

void hardwareInit() {
  robot.begin()
}

void enterCaptivePortal() {
  parseDataFromUsers() // IP Address & Port of the game server
}

void connectToGameServer() {
  wifi.begin()
}

void checkForCalibrationRequest() {
  if(calibrationRequested) {
    calibrate()
  }
}

void checkForServerMessage() {
  wifi.MessageReceived()
}