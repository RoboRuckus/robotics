#include <wifi_communication.hpp>

void WifiCommunication::begin() {
  // Local initialization. Once its business is done, there is no need to keep it around
  DNSServer dns;
  AsyncWiFiManager wifiManager(&server,&dns);

  checkForWifiInfoReset();
  checkForSavedWifiInformation();
  attemptWifiAutoConnect();

  // Read updated parameters
  // TODO: Why is this needed?
  strcpy(game_server, custom_game_server.getValue());
  strcpy(game_port, custom_game_port.getValue());
}

void checkForWifiInfoReset() {
  pinMode(RESET_PIN, INPUT_PULLUP);

  if (digitalRead(RESET_PIN) == LOW) {
    logger.write("Reset button held, resetting WiFi information");
    wifiManager.resetSettings();
    bot.showImage(Robot::images::Check, (Robot::colors)bot.robotColor);
    delay(2000);
    robot.reboot();
  }
}

void checkForSavedWifiInformation() {
  if (robot.fileExists("/wifi_config.json")) {
    logger.write("Reading WiFi config file")

    StaticJsonDocument<256> json = robot.readFile("/wifi_config.json")

    // Copy values from json file to variables
    strcpy(game_server, json["game_server"]);
    strcpy(game_port, json["game_port"]);
  } else {
    logger.write("No WiFi config file detected, skipping")
  }
}

void attemptWifiAutoConnect() {
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
    logger.write("Failed to connect and hit timeout");
    delay(3000);
    // Reset and try again, or maybe put it to deep sleep
    robot.reboot();
    delay(5000);
  }
}
