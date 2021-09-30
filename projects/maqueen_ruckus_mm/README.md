# RoboRuckus/MicroMayham

Here you'll find the relevant robot code to connect a robot to the [RoboRuckus game](https://www.roboruckus.com/).

## Deploying

The code is currently written in [MakeCode](https://makecode.microbit.org/).

1. First create a new project and add the MaqueenPlus extension.
2. Switch to Python editing and copy/paste the [Maqueen code](maqueen_ruckus_mm.py).
3. From the right-hand sidebar, open the explorer and delete the "radio" package.
4. Change any of the settings in the variables towards the top of the code as needed.
5. Enjoy!

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
Once the code has been deployed and the Wi-Fi module has been hooked-up, you can start up a RoboRuckus server following [these instructions](https://www.roboruckus.com/documentation/setting-up-the-game/). Be sure the Wi-fi SSID and WPA Password are the same on both the server and the code deployed to the Maqueen robot. Once the game server is up and running turn on the Maqueen. If everything connects properly, the Maqueen will show a smiley face on the front of the Micro:bit in 10-20 seconds. If it has trouble connecting it will show a frowny face instead.

If everything connected properly, set the Maqueen down on the edge of the game board and press the **A** button on the Micro:bit. The Maqueen will drive forward for four seconds adjusting the wheel speeds until they match. It will then drive backwards for four seconds and do the same. You can repeat this process at any time if the Maqueen seems to need recalibration. Calibration settings are not preserved when the Maqueen is switched off.

After calibration, you can test the Maqueen's movement by setting it on the board and pushing the **B** button on the Micro:bit. This will have the Maqueen drive a little test pattern, moving two squares forward, one square backward, turning right 90 degrees, left 90 degrees, then right 180 degrees.

If the Maqueen completes this sequence successfully, you're good to go. If it has trouble, you may need to adjust some of the movement timing variables near the top of the [Maqueen code](maqueen_ruckus_mm.py). You will then need to [re-deploy](https://github.com/tagnw/robotics/tree/main/projects/maqueen_ruckus_mm#deploying) the modified code to the Maqueen and repeat this calibration process.
