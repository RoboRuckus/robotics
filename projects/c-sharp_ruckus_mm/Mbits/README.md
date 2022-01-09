# RoboRuckus/MicroMayham C# Mbits

Here you'll find the relevant robot code to connect a C# and [nanoFramewoek](https://www.nanoframework.net/) based robot to the [RoboRuckus game](https://www.roboruckus.com/). RoboRuckus makes use of the [ESP32 Mbits platform](https://www.elecrow.com/mbits.html). Other ESP32 platforms may work, but they have not been tested. You'll find both the template for the Mbits microcontroller platform and any tested robot platforms here which also use the Mbits controller. 

## Deploying
1. Open the code in the [Visual Studio](https://docs.microsoft.com/en-us/visualstudio/install/install-visual-studio?view=vs-2022).
2. Install the nanoFramework extension for [Visual Studio](https://docs.nanoframework.net/content/getting-started-guides/getting-started-managed.html).
3. Flash the firmware to your platform with [nanoff] (https://docs.nanoframework.net/content/getting-started-guides/getting-started-managed.html#uploading-the-firmware-to-the-board-using-nanofirmwareflasher)
4. Download the folder with the solution you want for your platform or robot.
5. Open the solution in Visual Studio
6. Modify the code as needed.
7. Deploy or debug your code on your platform.
8. Enjoy!

## Template Structure
The template has three parts:
### The Robot Class
This class contains all the relevant robot code needed to control the robot itself. These are the methods you will need to modify:
#### Turn(int magnitude, int direction, int outOfTurn)
Called when the robot needs to turn. Modify to get your robot to turn to the correct magnitude of 90 degree incriments.
#### DriveForward(int magnitude, int outOfTurn)
Called when the robot needs to move forward. Modify to get your robot to move forward the correct magnitude of spaces.
#### DriveBackward(int magnitude, int outOfTurn)
Called when the robot needs to move backward. Modify to get your robot to move backward the correct magnitude of spaces.
#### pdateSettings(SettingsEventArgs e)
Modify this so that it saves movement and tuning parameters to the robot, optionally committing to persistent storage. See details on the structure of these settings strings below.
#### GetSettings(SettingsEventArgs e)
Modify this so it loads all the modifiable robot tuning and movement parameters to a JSON object which it returns. For more details on the JSON object, see below.

### The WiFi class
This class handles all the communication to the game server and parses and interprets messages from the game server. It shouldn't be necessary to modify this class as most everything should be handled by the Robot class.

### Program class
This class contains all the parameters and settings to connect to Wi-Fi and the game server, as well as GPIO pin configurtations. Modify as needed.

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

