using System;
using System.Diagnostics;
using System.Threading;
using Windows.Storage;
using System.Device.Gpio;
using WS2812;
using System.Device.Pwm;
using Iot.Device.ServoMotor;


namespace Mbits
{
    /// <summary>
    /// Defines a class for controlling a robot.
    /// </summary>
    public class Robot
    {
        /// <summary>
        /// The URL escaped robot name.
        /// </summary>
        public string RobotName => _robotName;

        /// <summary>
        /// Event triggers when the robot should go into demo mode on startup.
        /// </summary>
        public event EventHandler DemoMode;

        private MPU6050 _gyro;
        private StorageFolder _SPIFFS;
        private int _playerNumber = 0, _robotColor, _leftForwardSpeed, _rightForwardSpeed, _rightBackwardSpeed, _leftBackwardSpeed, _linearTime, _driftBoost, _drift;
        private string _robotName;
        private float _turnAngle;
        private int _buttonApin = 36, _buttonBpin = 39, _leftPin = 32, _rightPin = 25;
        GpioPin _buttonA, _buttonB;
        GpioController _gpio = new GpioController();
        PixelController _display;
        private images _currentImage;
        private bool _connected = false, _demoMode = false;

        private ServoMotor _left, _right;

        /// <summary>
        /// Image maps for display. Binary maps for each row, 1 on, 0 off.
        /// </summary>
        private byte[][] image_maps = {
            new byte[] { 0b00000, 0b00000, 0b00000, 0b00000, 0b00000 }, // Clear
            new byte[] { 0b00100, 0b01100 ,0b00100, 0b00100, 0b01110 }, // 1
            new byte[] { 0b11100, 0b00010, 0b01100, 0b10000, 0b11110 }, // 2
            new byte[] { 0b11110, 0b00010, 0b00100, 0b10010, 0b01100 }, // 3
            new byte[] { 0b00110, 0b01010, 0b10010, 0b11111, 0b00010 }, // 4
            new byte[] { 0b11111, 0b10000, 0b11110, 0b00001, 0b11110 }, // 5
            new byte[] { 0b00010, 0b00100, 0b01110, 0b10001, 0b01110 }, // 6
            new byte[] { 0b11111, 0b00010, 0b00100, 0b01000, 0b10000 }, // 7
            new byte[] { 0b01110, 0b10001, 0b01110, 0b10001, 0b01110 }, // 8
            new byte[] { 0b01110, 0b10001, 0b01110, 0b00100, 0b01000 }, // 9
            new byte[] { 0b01010, 0b01010, 0b00000, 0b10001, 0b01110 }, // Happy
            new byte[] { 0b01010, 0b01010, 0b00000, 0b01110, 0b10001 }, // Sad
            new byte[] { 0b01010, 0b00000, 0b00100, 0b01010, 0b00100 }, // Surprised
            new byte[] { 0b01100, 0b11100, 0b01111, 0b01110, 0b00000 }, // Duck
            new byte[] { 0b00000, 0b00001, 0b00010, 0b10100, 0b01000 }  // Check
        };

        /// <summary>
        /// Color maps for display.
        /// </summary>
        private byte[][] color_map = {
            new byte[] { 25, 0, 0 },  // Red
            new byte[] { 0, 12, 0 },  // Green
            new byte[] { 0, 0, 12 },  // Blue
            new byte[] { 12, 6, 0 },  // Yellow
            new byte[] { 12, 0, 9 },  // Purple
            new byte[] { 12, 4, 0 },  // Orange
            new byte[] { 0, 8, 12 },  // Cyan 
            new byte[] { 12, 12, 12 } // White
        };

        /// <summary>
        /// Enumeration of possible colors.
        /// </summary>
        private enum colors { Red, Green, Blue, Yellow, Purple, Orange, Cyan, White };

        /// <summary>
        /// Enumeration of images.
        /// </summary>
        private enum images { Clear, One, Two, Three, Four, Five, Six, Seven, Eight, Nine, Happy, Sad, Surprised, Duck, Check };

        /// <summary>
        /// Creates new robot object.
        /// </summary>
        public Robot()
        {
            // Create gyro object
            _gyro = new(gyroConfig: MPU6050.GyroRange.FiveHundred);

            // Find internal storage folder
            _SPIFFS = KnownFolders.InternalDevices.GetFolders()[0];

            // Initialize LEDs
            _display = new PixelController(13, 25); // Pin 13, 25 LEDs
            _display.TurnOff();

            // Load settings
            StorageFile file = null;
            try
            {
                file = _SPIFFS.CreateFile("settings.txt", CreationCollisionOption.OpenIfExists);
            }
            catch
            {
                Debug.WriteLine("Settings file does not exist yet.");
            }
            string curSettings = "";
            if (file != null)
            {
                // Attempt to read data from file
                try
                {
                    curSettings = FileIO.ReadText(file);
                }
                catch (Exception ex)
                {
                    Debug.WriteLine(ex.Message);
                }
            }
            // No saved settings
            if (curSettings == "" || curSettings is null)
            {
                // Save default settings
                UpdateSettings(new SettingsEventArgs("Test%20Bot,75,75,75,75,1200,5,10,90,0:", true));
            }
            else
            {
                // Apply loaded settings
                UpdateSettings(new SettingsEventArgs(curSettings));
            }

            // Load and/or save gyro calibration values to a file
            // Check if file exists
            file = null;
            try
            {
                file = _SPIFFS.CreateFile("gyroOffsets.txt", CreationCollisionOption.OpenIfExists);
            }
            catch
            {
                Debug.WriteLine("Gyro offsets file does not exist yet.");
            }
            curSettings = "";
            if (file != null)
            {
                // Attempt to read data from file
                try
                {
                    curSettings = FileIO.ReadText(file);
                }
                catch (Exception ex)
                {
                    Debug.WriteLine(ex.Message);
                }
            }
            // No saved offsets, calculate new ones
            if (curSettings == "" || curSettings is null)
            {
                float[] offsets = _gyro.calcGyroOffsets();
                StorageFile offsetsFile = _SPIFFS.CreateFile("gyroOffsets.txt", CreationCollisionOption.ReplaceExisting);
                FileIO.WriteText(offsetsFile, offsets[0].ToString() + "," + offsets[1].ToString() + "," + offsets[2].ToString());
            }
            else
            {
                // Update gyro with saved offsets
                string[] offsets = curSettings.Split(',');
                _gyro.calcGyroOffsets(float.Parse(offsets[0]), float.Parse(offsets[1]), float.Parse(offsets[2]));
            }

            // Configure buttons
            _buttonA = _gpio.OpenPin(_buttonApin, PinMode.InputPullUp);
            _buttonA.DebounceTimeout = new TimeSpan(0, 0, 0, 0, 15); // 15 ms debounce filter
            _buttonA.ValueChanged += buttonA_Pressed;

            _buttonB = _gpio.OpenPin(_buttonBpin, PinMode.InputPullUp);
            _buttonB.DebounceTimeout = new TimeSpan(0, 0, 0, 0, 15);
            _buttonB.ValueChanged += buttonB_Pressed;
        }

        /// <summary>
        /// Deletes the settings file, or runs a demo navigation test.
        /// </summary>
        /// <param name="sender"></param>
        /// <param name="e"></param>
        private void buttonA_Pressed(object sender, PinValueChangedEventArgs e)
        {
            if (e.ChangeType == PinEventTypes.Falling)
            {
                // Check if connected to determine what to do next
                if (_connected)
                {
                    Debug.WriteLine("Deleting settings file.");
                    StorageFile file = null;
                    try
                    {
                        file = _SPIFFS.CreateFile("settings.txt", CreationCollisionOption.OpenIfExists);
                    }
                    catch
                    {
                        Debug.WriteLine("Settings file does not exist.");
                    }

                    if (file != null)
                    {
                        file.Delete();
                    }
                    showImage(images.Check, (colors)_robotColor);
                    Thread.Sleep(2000);
                    showImage(_currentImage, (colors)_robotColor);
                }
                else
                {
                    Debug.WriteLine("Entering demo mode, this may take up to 20 seconds...");
                    // Run a demo mode
                    _demoMode = true;
                    DemoMode?.Invoke(this, EventArgs.Empty);
                    showImage(images.Duck, (colors)_robotColor, true);
                }
            }

        }

        /// <summary>
        /// Deletes the gyro offsets file.
        /// </summary>
        /// <param name="sender"></param>
        /// <param name="e"></param>
        private void buttonB_Pressed(object sender, PinValueChangedEventArgs e)
        {
            if (e.ChangeType == PinEventTypes.Falling)
            {
                Debug.WriteLine("Deleting gyro offsets file.");
                StorageFile file = null;
                try
                {
                    file = _SPIFFS.CreateFile("gyroOffsets.txt", CreationCollisionOption.OpenIfExists);
                }
                catch
                {
                    Debug.WriteLine("Gyro offsets file does not exist.");
                }

                if (file != null)
                {
                    file.Delete();
                }
                showImage(images.Check, (colors)_robotColor);
                Thread.Sleep(2000);
                showImage(_currentImage, (colors)_robotColor);
            }

        }

        /// <summary>
        /// Has the robot react to being assigned to a player.
        /// </summary>
        /// <param name="playerNumber">The player number the robot is assigned to.</param>
        public void PlayerAssigned(int playerNumber)
        {
            _playerNumber = playerNumber;
            showImage((images)playerNumber, (colors)_robotColor, true);
        }

        /// <summary>
        /// Has the robot drive forward.
        /// </summary>
        /// <param name="magnitude">The number of spaces to drive forward.</param>
        /// <param name="outOfTurn">If the move is not on the robot's turn.</param>
        public void DriveForward(int magnitude, int outOfTurn)
        {
            
        }

        /// <summary>
        /// Has the drive backward.
        /// </summary>
        /// <param name="magnitude">The number of spaces to drive.</param>
        /// <param name="outOfTurn">If the move is not on the robot's turn.</param>
        public void DriveBackward(int magnitude, int outOfTurn)
        {
            
        }

        /// <summary>
        /// Has the robot turn.
        /// </summary>
        /// <param name="magnitude">The number of 90 degree segments to turn.</param>
        /// <param name="direction">The direction of the turn. 0 = right, 1 = left.</param>
        /// <param name="outOfTurn">If the move is not on the robot's turn.</param>
        public void Turn(int magnitude, int direction, int outOfTurn)
        {
            
        }

        /// <summary>
        /// Has the robot react to attempting a move that has been blocked.
        /// </summary>
        /// <param name="sender"></param>
        /// <param name="e"></param>
        public void Blocked(object sender, EventArgs e)
        {
            showImage(images.Surprised, (colors)_robotColor);
            Thread.Sleep(1500);
            showImage(_currentImage,(colors)_robotColor);
        }

        /// <summary>
        /// Has the robot react to taking damage.
        /// </summary>
        /// <param name="amount">The total amount of damage that has been taken.</param>
        public void TakeDamage(int amount)
        {
            showImage(images.Surprised, (colors)_robotColor);
            Thread.Sleep(1500);
            showImage(_currentImage, (colors)_robotColor);
        }

        /// <summary>
        /// Has the robot perform a speed test.
        /// </summary>
        /// <param name="sender"></param>
        /// <param name="e"></param>
        public void SpeedTest(object sender, EventArgs e)
        {
            DriveForward(3, 0);
            Thread.Sleep(1000);
            DriveBackward(3, 0);
        }

        /// <summary>
        /// Has the robot perform a navigation test.
        /// </summary>
        /// <param name="sender"></param>
        /// <param name="e"></param>
        public void NavigationTest(object sender, EventArgs e)
        {
            DriveForward(2, 0);
            Thread.Sleep(1000);
            DriveBackward(1, 0);
            Thread.Sleep(1000);
            Turn(1, 0, 0);
            Thread.Sleep(1000);
            Turn(1, 1, 0);
            Thread.Sleep(1000);
            Turn(2, 0, 0);
        }

        /// <summary>
        /// Has the robot react to the entering or leaving Setup Mode.
        /// </summary>
        /// <param name="exiting">If the robot is leaving Setup Mode.</param>
        public void SetupModeStateChange(bool exiting)
        {
            if (exiting)
            {
                showImage(images.Happy, (colors)_robotColor, true);
            }
            else
            {
                showImage(images.Duck, (colors)_robotColor, true);
            }
        }

        /// <summary>
        /// Resets the robot state to the initial state.
        /// </summary>
        /// <param name="sender"></param>
        /// <param name="e"></param>
        public void Reset(object sender, EventArgs e)
        {
            _playerNumber = 0;
            showImage(images.Happy, (colors)_robotColor, true);
        }

        /// <summary>
        /// Retrieves the current robot settings.
        /// </summary>
        /// <param name="e">The settings parameters.</param>
        public void GetSettings(SettingsEventArgs e)
        {
            string output = "{\"name\": \"";
            output += _robotName;
            output += "\", \"controls\": [{ \"name\": \"leftForwardSpeed\", \"displayname\": \"Left Forward Speed\", \"min\": 0, \"max\": 90, \"increment\": 1, \"current\":";
            output += (_leftForwardSpeed - 90).ToString();
            output += "},{ \"name\": \"rightForwardSpeed\", \"displayname\": \"Right Forward Speed\", \"min\": 0, \"max\": 90, \"increment\": 1, \"current\":";
            output += (90 - _rightForwardSpeed).ToString();
            output += "},{ \"name\": \"leftBackwardSpeed\", \"displayname\": \"Left Backward Speed\", \"min\": 0, \"max\": 90, \"increment\": 1, \"current\":";
            output += (90 - _leftBackwardSpeed).ToString();
            output += "},{ \"name\": \"rightBackwardSpeed\", \"displayname\": \"Right Backward Speed\", \"min\": 0, \"max\": 90, \"increment\": 1, \"current\":";
            output += (_rightBackwardSpeed - 90).ToString();
            output += "},{ \"name\": \"linearTime\", \"displayname\": \"Linear Movement Time\", \"min\": 500, \"max\": 2000, \"increment\": 10, \"current\":";
            output += _linearTime.ToString();
            output += "},{ \"name\": \"drift\", \"displayname\": \"Drift Limit\", \"min\": 0, \"max\": 15, \"increment\": 1, \"current\":";
            output += _drift.ToString();
            output += "},{ \"name\": \"driftBoost\", \"displayname\": \"Drift Boost\", \"min\": 0, \"max\": 20, \"increment\": 1, \"current\":";
            output += _driftBoost.ToString();
            output += "},{ \"name\": \"turnAngle\", \"displayname\": \"Turn Angle\", \"min\": 60, \"max\": 120, \"increment\": 0.5, \"current\":";
            output += _turnAngle.ToString();
            output += "},{ \"name\": \"robotColor\", \"displayname\": \"Color\", \"min\": 0, \"max\": 7, \"increment\": 1, \"current\":";
            output += _robotColor.ToString();
            output += "}]}";

            e.Settings = output;
        }

        /// <summary>
        /// Updates the robots settings.
        /// </summary>
        /// <param name="e">The settings parameters.</param>
        public void UpdateSettings(SettingsEventArgs e)
        {
            // Parse settings string and remove terminal colon character
            string[] newSettings = e.Settings.Substring(0, e.Settings.Length - 1).Split(',');

            /* 
            * Assign new values.
            * The motor speed is set via the Servo library, which uses a value between 0-180.
            * At the middle value, 90, the motors don't turn, above that value the motors
            * turn one direction increasing in speed the further from 90. Below 90 is the same
            * only the wheels turn the opposite direction. To let the user set a value from 0-90
            * with 90 being the fastest, you need to subtract each value from 90 when receiving 
            * or sending the value if the desired setting is below 90. For wheels that need to
            * have values above 90, 90 must be added.
            */
            _robotName = newSettings[0];
            _leftForwardSpeed = int.Parse(newSettings[1]) + 90;
            _rightForwardSpeed = 90 - int.Parse(newSettings[2]);
            _leftBackwardSpeed = 90 - int.Parse(newSettings[3]);
            _rightBackwardSpeed = int.Parse(newSettings[4]) + 90;
            _linearTime = int.Parse(newSettings[5]);
            _drift = int.Parse(newSettings[6]);
            _driftBoost = int.Parse(newSettings[7]);
            _turnAngle = float.Parse(newSettings[8]);
            _robotColor = int.Parse(newSettings[9]);

            if (e.Commit)
            {
                StorageFile settingsFile = _SPIFFS.CreateFile("settings.txt", CreationCollisionOption.ReplaceExisting);
                try
                {
                    FileIO.WriteText(settingsFile, e.Settings);
                }
                catch (Exception ex)
                {
                    Debug.WriteLine(ex.Message);
                }
            }
            // Update the screen with the new color
            showImage(_currentImage, (colors)_robotColor);
        }

        /// <summary>
        /// Has the robot react to a connection attempt.
        /// </summary>
        /// <param name="success">If the attempt was successful.</param>
        public void ConnectionResult(bool success)
        {
            if (!_demoMode)
            {
                if (success)
                {
                    showImage(images.Happy, (colors)_robotColor, true);
                    _connected = true;
                }
                else
                {
                    showImage(images.Sad, (colors)_robotColor, true);
                    _connected = false;
                }
            }
        }

        /// <summary>
        /// Display an image on the LED screen.
        /// </summary>
        /// <param name="image">The image to display.</param>
        /// <param name="color">The color of the image.</param>
        /// <param name="saveImage">Save the image as the current default image.</param>
        private void showImage(images image, colors color, bool saveImage = false)
        {
            Display(image_maps[(int)image], color_map[(int)color], _display);
            if (saveImage)
                _currentImage = image;
        }

        /// <summary>
        /// Pushes colors to a set of WS2812 LEDs.
        /// </summary>
        /// <param name="image">The byte array encoding the image.</param>
        /// <param name="color">the R,G,B color as a byte array.</param>
        /// <param name="controller">The PixelController that the LEDs are on.</param>
        private void Display(byte[] image, byte[] color, PixelController controller)
        {
            for (int c = 0; c < 5; c++)
            {
                for (int r = 0; r < 5; r++)
                {
                    if (((image[c] >> r) & 0x01) == 1)
                    {
                        // Set the LED color at the given column and row
                        controller.SetColor((short)(c * 5 + 4 - r), color[0], color[1], color[2]);
                    }
                    else
                    {
                        controller.SetColor((short)(c * 5 + 4 - r), 0, 0, 0);
                    }
                }
            }
            controller.UpdatePixels();
        }
    }
}