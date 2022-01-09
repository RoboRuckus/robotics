using System.Threading;
using nanoFramework.Hardware.Esp32;

namespace RingbitCar
{
    public class Program
    {
        private static WiFiCommunicator _wifi;
        private static Robot _robot;

        // Network settings
        private static string SSID = "RoboRuckus";
        private static string Password = "Password";
        private static string ServerIP = "192.168.3.1";
        private static string ServerPort = "8082";

        // Used to enter demo mode
        private static bool _demoMode = false; 

        public static void Main()
        {
            // Configure I2C pins
            Configuration.SetPinFunction(Gpio.IO21, DeviceFunction.I2C1_CLOCK);
            Configuration.SetPinFunction(Gpio.IO22, DeviceFunction.I2C1_DATA);

            // Configure PWM pins
            Configuration.SetPinFunction(Gpio.IO25, DeviceFunction.PWM3);
            Configuration.SetPinFunction(Gpio.IO32, DeviceFunction.PWM2);

            // Create robot object
            _robot = new Robot();

            // Subscribe demo mode event handler
            _robot.DemoMode += _robot_DemoMode;

            // Create WiFi communicator  object
            _wifi = new WiFiCommunicator(SSID, Password, ServerIP, ServerPort);

            // Subscribe event handlers
            _wifi.ConnectionResult += _robot.ConnectionResult;
            _wifi.PlayerAssigned += _robot.PlayerAssigned;
            _wifi.GetSettings += _robot.GetSettings;
            _wifi.UpdateSettings += _robot.UpdateSettings;
            _wifi.Reset += _robot.Reset;
            _wifi.SetupModeState += _robot.SetupModeStateChange;
            _wifi.DriveForward += _robot.DriveForward;
            _wifi.DriveBackward += _robot.DriveBackward;
            _wifi.Turn += _robot.Turn;
            _wifi.BlockedMove += _robot.Blocked;
            _wifi.TakeDamage += _robot.TakeDamage;
            _wifi.SpeedTest += _robot.SpeedTest;
            _wifi.NavigationTest += _robot.NavigationTest;

            // Connect to game server, exit if demo mode is enabled
            while (!_demoMode && !_wifi.Connect(_robot.RobotName))
            {
                Thread.Sleep(1000);
            }

            // Check if robot should be in demo mode
            if (_demoMode)
            {
                while (true)
                {
                    // Drive in a lawnmower pattern
                    _robot.DriveForward(4, 0);
                    Thread.Sleep(250);
                    _robot.Turn(1, 1, 0);
                    Thread.Sleep(250);
                    _robot.DriveForward(1, 0);
                    Thread.Sleep(250);
                    _robot.Turn(1, 1, 0);
                    Thread.Sleep(250);

                    _robot.DriveForward(4, 0);
                    Thread.Sleep(250);
                    _robot.Turn(1, 0, 0);
                    Thread.Sleep(250);
                    _robot.DriveForward(1, 0);
                    Thread.Sleep(250);
                    _robot.Turn(1, 0, 0);
                }
            }

            // Listen for incoming commands from game server
            while (true)
            {
                _wifi.ServerListen();
                Thread.Sleep(50);
            }
        }

        /// <summary>
        /// Enables robot demo mode.
        /// </summary>
        /// <param name="sender"></param>
        /// <param name="e"></param>
        private static void _robot_DemoMode(object sender, System.EventArgs e)
        {
            _demoMode = true;
        }
    }
}