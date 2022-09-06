#include <robot.hpp>

void Robot::begin() {
  logger.write("Initializing Robot")
  Wire.begin(22,21);
}

void Robot::reboot() {
  ESP.restart();
}

bool Robot::fileExists(String filename) {
  return SPIFFS.exists(filename)
}

StaticJsonDocument<256> Robot::readFile(String filename) {
  if (this->fileExists(filename))
  {
    logger.write(filename + " exists, opening file")
    File configFile = SPIFFS.open(filename, "r");
    if (configFile)
    {
      logger.write(filename + " opened, reading json data")

      size_t size = configFile.size();
      // Allocate a buffer to store contents of the file.
      char buf[size];
      // Create JSON object to hold data
      StaticJsonDocument<256> json;
      // Read the file
      configFile.readBytes(buf, size);
      configFile.close();
      // Capture error status of json blob
      DeserializationError result = deserializeJson(json, buf);
      // Print to serial port what was loaded
      serializeJson(json, Serial);

      if (result.code() == DeserializationError::Ok)
      {
        logger.write(filename + " successfully parsed");
        return json;
      }
      else
      {
        logger.write("Failed to load " + filename);
        return NULL;
      }
    }
  }
}
