# RoboRuckus/MicroMayham Maqueen

Here you'll find the relevant robot code to connect a Maqueen robot to the [RoboRuckus game](https://www.roboruckus.com/).

## Deploying

### μPython
[This code](maqueen_ruckus_uPython.py) is written in μPython.
1. Download an appropriate IDE, the [Mu Editor](https://codewith.mu/) is recommended.
2. Open the editor and put it in `BBC micro:bit` mode.
3. Copy and paste the [maqueen_ruckus_uPython.py](maqueen_ruckus_uPython.py) code.
4. Change the Wi-Fi and server settings at top of the code as needed (see [Connecting and Calibrating](https://github.com/tagnw/robotics/tree/main/projects/maqueen_ruckus_mm#connecting-and-calibrating)).
5. Plug in your Micro:bit to your computer via USB and press the `Flash` button in Mu.
6. Enjoy!

### Make Code
[This code](https://github.com/tagnw/robotics/blob/main/projects/maqueen_ruckus_mm/maqueen_ruckus_MakeCode.py) is written in [MakeCode](https://makecode.microbit.org/).

1. First create a new project and add the MaqueenPlus extension.
2. Switch to Python editing and copy/paste the [maqueen_ruckus_MakeCode.py](maqueen_ruckus_MakeCode.py) code.
3. Change the [RobotName](https://github.com/tagnw/robotics/blob/main/projects/maqueen_ruckus_mm/maqueen_ruckus_MakeCode.py#L15) to something unique to this robot. Must be [URL escaped](https://www.december.com/html/spec/esccodes.html).
4. Optioanlly, change the [robot's LED color](https://github.com/tagnw/robotics/blob/main/projects/maqueen_ruckus_mm/maqueen_ruckus_MakeCode.py#L6).
5. From the right-hand sidebar, open the explorer and delete the "radio" package.
6. Change any of the settings in the variables towards the top of the code as needed (see [Connecting and Calibrating](https://github.com/tagnw/robotics/tree/main/projects/maqueen_ruckus_mm#connecting-and-calibrating)).
7. Plug in your Micro:bit to your computer via USB and download the code from the MakeCode website to your Micro:bit.
8. Enjoy!

## Wiring up Wi-Fi Module
RoboRuckus makes use of the [ESP8266 Wi-Fi module](https://www.sparkfun.com/products/17146), specifically the ESP-01S version of the module. Wire the Wi-Fi module to the Maqueen using [Female-Female](https://www.sparkfun.com/products/11710) jumpers in the following way:

```
ESP ------ Maqueen
TX  ------ P1
RX  ------ P2
3V3 ------ 3V3
GND ------ GND
```

## Connecting and Calibrating
### Setup RoboRuckus
Once the code has been deployed and the Wi-Fi module has been hooked-up, you can start up a RoboRuckus server following [these instructions](https://www.roboruckus.com/documentation/setting-up-the-game/). Be sure the Wi-fi SSID and WPA Password are the same on both the server and the code deployed to the Maqueen robot. Once the game server is up and running turn on the Maqueen. If everything connects properly, the Maqueen will show a smiley face on the front of the Micro:bit in 10-20 seconds. If it has trouble connecting it will show a frowny face instead.

If the robot is reconnecting after losing power or being switched off in the middle of a game, it may receive an erroneous movement command. This is fine and the robot should be good to go after it finishes this movement.

### Calibration
If you are using the μPython version of the code, and **only** the μPython version of the code, you can use the RoboRuckus server to [tune the robots](https://www.roboruckus.com/documentation/running-a-game/#Tuning-the-Robots). Note that the actual tuning options presented will be different depending on the robot design being used. For the Maqueen you will have the options to tune the variables [described below](https://github.com/tagnw/robotics/tree/main/projects/maqueen_ruckus_mm#tuning-variables). You can also set the LED colors for the robot. For details on deploying your own tuning options for other robots designs, see [below](https://github.com/tagnw/robotics/tree/main/projects/maqueen_ruckus_mm#custom-tuning-options).

The `Speed Test` button will also calibrate the wheel speeds as described [below](https://github.com/tagnw/robotics/tree/main/projects/maqueen_ruckus_mm#wheel-speed-calibration), pushing the **A** button will also work identically to what's described below.

### Wheel Speed Calibration
If everything connected properly, set the Maqueen down on the edge of the game board and press the **A** button on the Micro:bit. The Maqueen will drive forward for four seconds adjusting the wheel speeds until they match. It will then drive backwards for four seconds and do the same. You can repeat this process at any time if the Maqueen seems to need recalibration. Calibration settings are not preserved when the Maqueen is switched off.

### Tuning Movement
If you are using the MakeCode version of the code, and **only** the MakeCode version, after calibration, you can test the Maqueen's movement by setting it on the board and pushing the **B** button on the Micro:bit. This will have the Maqueen drive a little test pattern, moving two squares forward, one square backward, turning right 90 degrees, left 90 degrees, then right 180 degrees.

If the Maqueen completes this sequence successfully, you're good to go. If it has trouble, you may need to adjust some of the movement timing variables near the top of the [Maqueen code](maqueen_ruckus_mm.py). You will then need to [re-deploy](https://github.com/tagnw/robotics/tree/main/projects/maqueen_ruckus_mm#deploying) the modified code to the Maqueen and repeat this calibration process.

### Tuning Variables
The vairables to tune are as follows:
| Variable | Description |
| ----------- | ----------- |
| LinearSpeedTarget | The speed each wheel will be tuned to move at when calibrated. Higher values mean faster movement. |
| LinearTime | Timeout, in milliseconds, that will cause the robot to end the move. Used so that if the robot gets stuck or otherwise can't complete the move it won't prevent the game from continuing. |
| LinearDistance | The number of wheel rotations required for the robot to move one square on the game board. |
| TurnDistance | The number of wheel rotations required of each wheel during the turn sequence. |

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
The new robot name is always first in the list, and the remaining values are what are described by the [JSON object below](https://github.com/tagnw/robotics/tree/main/projects/maqueen_ruckus_mm#the-json-object).
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

For example, the complete default JSON object for the Maqueen is:
```
{"name": "Test%20Bot", "controls": [ 
	{ "name": "LinearSpeedTarget", "displayname": "Speed", "min": 50, "max": 150, "increment": 1, "current": 100},
	{ "name": "LinearTime", "displayname": "Max travel time (ms)", "min": 800, "max": 1500, "increment": 10, "current": 1300},
	{ "name": "LinearDistance", "displayname": "Travel distance", "min": 0.2, "max": 1.2, "increment": 0.01, "current": 0.72},
	{ "name": "TurnDistance", "displayname": "Turn distance", "min": 0.2, "max": 1.2, "increment": 0.01, "current": 0.32},
	{ "name": "color", "displayname": "LED Color", "min": 1, "max": 7, "increment": 1, "current": 4}]}
```

## To Do
- Test and finetune robot movement.
- Add self-correction either via compass module, line following, or both.
- <strike>Add support for RoboRuckus bot tuning via server front end, including [persistent storing of settings](https://lancaster-university.github.io/microbit-docs/archive/v2.1.0/ubit/storage/).</strike>
- <strike>Convert from MakeCode to pure uPython.</strike>
- Add custom extension and blocks for MakeCode, EduBlocks, or similar.
