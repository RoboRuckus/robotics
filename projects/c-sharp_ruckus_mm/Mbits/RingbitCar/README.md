# RoboRuckus/MicroMayham Ring:bit Car V2

Here you'll find the relevant robot code to connect a C# and [nanoFramewoek](https://www.nanoframework.net/) based robot to the [RoboRuckus game](https://www.roboruckus.com/). This code is for the [ESP32 Mbits platform](https://www.elecrow.com/mbits.html) and the [Ring:bit Car V2](https://www.elecfreaks.com/ring-bit-car-v2-for-micro-bit.html).

## Deploying
Please see the Mbits template for deployment instructions.

When deploying the firmware, use this command:

```
nanoff --update --target ESP32_PSRAM_REV0 --serialport COM3 --preview -fwversion 1.7.3-preview.225
```

Substituting `COM3` with the COM port of your Mbits.

## Wiring up the Ring:bit Car
Connect the servo and bottom expansion board to the back connectiors as follows:
| Device | Connector |
| ----------- | ----------- |
| Expansion board | 0VG |
| Left servo | 1VG |
| Right servo | 2VG |

## Buttons
The A amd B buttons on the front of the Mbits have the following functions:

### A Button
If the robot is not connected to the game server (displaying a frowny face) pushing this button will put the robot into a demo mode where it will drive in a lawnmower pattern (back and forth) until it is rebooted. If the robot is connected to the server, pushing this button will delete any saved robot tuning parameters saved on the device.

### B Button
Pushing this button will delete any saved gyroscope calibration factors saved on the device. These calibration factors will be regenerated the next time the device is rebooted. It's important not to move the robot during that process, wait for a smiley or frowny face to know the calibration process is complete.