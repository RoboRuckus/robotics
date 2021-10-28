# RoboRuckus/MicroMayham

Here you'll find the relevant robot code to connect an Arduino based robot to the [RoboRuckus game](https://www.roboruckus.com/).

## Deploying
1. Open the code in the [Arduino IDE](https://www.arduino.cc/en/Guide) or IDE of choice.
2. Copy the contents of the [template](https://github.com/tagnw/robotics/blob/main/projects/arduino_ruckus_mm/ruckus_mm_template.ino) to the IDE.
3. Modify the code to suit your robot (details below).
4. Flash to your robot.
5. Enjoy!

## Wiring up Wi-Fi Module
RoboRuckus makes use of the [ESP8266 Wi-Fi module](https://www.sparkfun.com/products/17146), specifically the ESP-01S version of the module. Wire the Wi-Fi module to the Arduino in the following way:

```
ESP ------ Arduino
TX  ------ RX (Pin D0 on Arduino Uno)
RX  ------ TX (Pin D1 on Arduino Uno)
3V3 ------ 3V3
GND ------ GND
```

## Template Structure
The template has three parts starting from the top/
### The Robot Class
This class contains all the relevant robot code needed to control the robot itself. These are the methods:
#### playerAssigned(int player)
Called when a player is assigned to the robot. Modify this to display the player number if desired.
#### turn(int direction, int magnitude)
Called when the robot needs to turn. Modify to get your robot to turn to correct magnitude of 90 degree incriments.
#### driveForward(int magnitude)
Called when the robot needs to move forward. Modify to get your robot to move forward to correct magnitude of spaces.
#### driveBackward(int magnitude)
Called when the robot needs to move backward. Modify to get your robot to move backward to correct magnitude of spaces.
#### blockedMove()
Optionally, modify this to have the robot react if it instructed to move but is blacked by, for example, a wall.
#### takeDamage(int amount)
Optionally, modify this to have your robot react to taking damage. Amount is the total amount of damage suffered so far.

#### saveSettings(String settings, bool commit)
Modify this so that it saves movement and tuning parameters to the robot, optionally committing to persistent storage like EEPROM. See details on the structure of these settings strings below.

#### loadSettings()
Modify this so it loads all the modifiable robot tuning and movement parameters to a JSON object which it returns. For more details on the JSON object, see below.

#### speedTest()
Drives the robot forwards and backwards to test moving in a straight line.

#### navigationTest()
Runs a navigation test to see how the robot performs.

#### reset()
Called when the game is reset. Modify to do whatever is needed to return to the initial state.

### The WiFi class
This class handles all the communication to the game server and parses and interprets messages from the game server. It shouldn't be necessary to modify this class as most everything should be handled by the Robot class.

### Arduino setup() and loop()

Towards the bottom you'll find the places where the WiFi and Robot classes are initialized and the parameters (such as WiFI SSID and password) that they use. You should update these parameters to match what you are using. You should also include any robot specific setup code here for your robot design.

The loop function shouldn't need modification unless specific to your robot design. It will continually check for a message from the server and then pass it to the WiFi class for processing.

### Custom Tuning Options
When a robot is not assigned to a player and receives a `1:` message from the game server, it will enter tuning mode. There it will wait for further instructions of the form `option:data` where `option` is an instruction as described in the below table. The `data` portion is addressed below the table.
| Option | Description |
| ----------- | ----------- |
| 0 | Send the tuning JSON object to the server (see below). |
| 1 | Save the tuning settings from  `data` and run a speed test. |
| 2 | Save the tuning settings from  `data` and run a calibration test. |
| 3 | Save the tuning settings from  `data` to persistent storage and exit tuning mode. |

The `data` sent by the server is a comma separated string of the new tuning variable values and is terminated by a `:`, for example:
```
RobotName,value_1,value_2,...,value_n:
```
The new robot name is always first in the list, and the remaining values are what are described by the JSON object below.
#### The JSON object
This JSON string is used by a bot to inform the server of what tuning parameters are available to be adjusted and what their current values are. The object has the form:
```
{"name": "Test%20Bot", "controls": [ 
  { "name":"value_1", "displayname": "Parameter 1", "min": 0, "max": 180, "increment": 1, "current": 93},
  { "name": "value_2", "displayname": "Parameter 2", "min": -10, "max": 10, "increment": 1, "current": 0},
  ...
  { "name": "value_n", "displayname": "Parameter n", "min": 0, "max": 2, "increment": 0.1, "current": 0.5}]}
```
Please note that the formatting is important, the JSON string must end wtih the sequence `}]}`. Each object must include the robot name first, and then a list of controls each with the following attributes:
| Attribute | Description |
| ----------- | ----------- |
| name | The variable name, should include no spaces or other special characters except `-` or `_` |
| displayname | A friendly name to show to the user on the interface. |
| min | The minimum value the parameter can have. |
| max | The maximum value the parameter can have. |
| increment | The size of each step when adjusting the slider on the interface. |
| current | The current value of the parameter on the bot. |

For example, the complete default JSON object for the Maqueen robot is:
```
{"name": "Test%20Bot", "controls": [ 
	{ "name": "LinearSpeedTarget", "displayname": "Speed", "min": 50, "max": 150, "increment": 1, "current": 100},
	{ "name": "LinearTime", "displayname": "Max travel time (ms)", "min": 800, "max": 1500, "increment": 10, "current": 1300},
	{ "name": "LinearDistance", "displayname": "Travel distance", "min": 0.2, "max": 1.2, "increment": 0.01, "current": 0.72},
	{ "name": "TurnDistance", "displayname": "Turn distance", "min": 0.2, "max": 1.2, "increment": 0.01, "current": 0.32},
	{ "name": "color", "displayname": "LED Color", "min": 1, "max": 7, "increment": 1, "current": 4}]}
```

