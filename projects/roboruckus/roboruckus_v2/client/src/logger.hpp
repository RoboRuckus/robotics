#ifndef LOGGER_HPP
#define LOGGER_HPP

#define LOGGER_SERIAL_BAUD_RATE 115200

class Logger {
public:
  void begin();
  void write(String output);
}

#endif
