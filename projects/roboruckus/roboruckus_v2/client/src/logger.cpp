#include <logger.hpp>

void Logger::begin() {
  // TODO: Prevent calling twice causing issues
  Serial.begin(LOGGER_SERIAL_BAUD_RATE);
  this->write("RoboRuckus Client Logger Starting...");
}

void Logger::write(String output) {
  Serial.println(output);
}
