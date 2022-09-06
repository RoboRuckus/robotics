#ifndef ROBOT_HPP
#define ROBOT_HPP

class Robot {
public:
  void begin();
  void reboot();
  bool fileExists(String filename);
  StaticJsonDocument<256> readFile(String filename);
}

#endif
