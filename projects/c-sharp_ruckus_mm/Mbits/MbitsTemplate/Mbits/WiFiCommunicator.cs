using System;
using System.Device.WiFi;
using System.Net;
using System.Net.Sockets;
using System.Net.NetworkInformation;
using System.Diagnostics;
using System.Threading;
using System.Text;

namespace Mbits
{
    /// <summary>
    /// Class that handles communicating with game server over WiFi.
    /// </summary>
    public class WiFiCommunicator
    {
        // Custom event delegates
        public delegate void PlayerAssignedHandler(int playerNumber);
        public delegate void DriveForwardHandler(int magnitude, int outOfTurn);
        public delegate void DriveBackwardHandler(int magnitude, int outOfTur);
        public delegate void TurnHandler(int magnitude, int direction, int outOfTur);
        public delegate void TakeDamageHandler(int amount);
        public delegate void SetupModeHandler(bool exiting);
        public delegate void GetSettingsHandler(SettingsEventArgs e);
        public delegate void UpdateSettingsHandler(SettingsEventArgs e);
        public delegate void ConnectionResultHandler(bool connected);

        /// <summary>
        /// Fires when a player is assigned.
        /// </summary>
        public event PlayerAssignedHandler PlayerAssigned;

        /// <summary>
        /// Fires when a drive forward command is received.
        /// </summary>
        public event DriveForwardHandler DriveForward;

        /// <summary>
        /// Fires when a drive backward command is received.
        /// </summary>
        public event DriveBackwardHandler DriveBackward;

        /// <summary>
        /// Fires when a turn command is received.
        /// </summary>
        public event TurnHandler Turn;

        /// <summary>
        /// Fires when the robot takes damage.
        /// </summary>
        public event TakeDamageHandler TakeDamage;

        /// <summary>
        /// Fires when entering or leaving setup mode.
        /// </summary>
        public event SetupModeHandler SetupModeState;

        /// <summary>
        /// Fires when the robot settings need to be retrieved.
        /// </summary>
        public event GetSettingsHandler GetSettings;

        /// <summary>
        /// Fires when updating the settings.
        /// </summary>
        public event UpdateSettingsHandler UpdateSettings;

        /// <summary>
        /// Fires when a reset command is received.
        /// </summary>
        public event EventHandler Reset;

        /// <summary>
        /// Fires when the bot's move is blocked.
        /// </summary>
        public event EventHandler BlockedMove;

        /// <summary>
        /// Fires when the bot needs to perform a navigation test.
        /// </summary>
        public event EventHandler NavigationTest;

        /// <summary>
        /// Fires when the bot needs to perform a speed test.
        /// </summary>
        public event EventHandler SpeedTest;

        /// <summary>
        /// Fires after a connection attempt is made with the result of the attempt
        /// </summary>
        public event ConnectionResultHandler ConnectionResult;


        /// <summary>
        /// The number assigned to the bot (can probably be private)
        /// </summary>
        public string BotNumber => _botNumber;

        // Private variables
        private WiFiAdapter _wifi;
        private string _ssid, _password, _serverAddress, _port, _botNumber;
        private bool _started = false, _inSetupMode = false;
        private NetworkInterface _interface;
        Socket _listener;
        private int _adapterNumber;

        /// <summary>
        /// Constructs a new WiFi Communicator object.
        /// </summary>
        /// <param name="SSID">The SSID of the network to connect to.</param>
        /// <param name="Password">The password of the network to connect to.</param>
        /// <param name="ServerAddress">The address of the gamer server.</param>
        /// <param name="ServerPort">The port of the game server.</param>
        /// <param name="AdapterNumber">The network adapter to use.</param>
        public WiFiCommunicator(string SSID, string Password, string ServerAddress, string ServerPort, int AdapterNumber = 0)
        {
            // Get the adapter
            _adapterNumber = AdapterNumber;
            _wifi = WiFiAdapter.FindAllAdapters()[_adapterNumber];
            // Get the network interface of the adapter
            _interface = NetworkInterface.GetAllNetworkInterfaces()[_wifi.NetworkInterface];

            // Assign variables
            _ssid = SSID;
            _password = Password;
            _serverAddress = ServerAddress;
            _port = ServerPort;
        }

        /// <summary>
        /// Connect to the game server and inform server of the bot.
        /// </summary>
        /// <param name="RobotName">The URL escaped robot name.</param>
        /// <returns>True on success.</returns>
        public bool Connect(string RobotName)
        {
            Debug.WriteLine("Attempting to connect to game server.");

            // Disconnect to be safe
            _wifi.Disconnect();

            // Try connecting to WiFi network
            WiFiConnectionResult result = _wifi.Connect(_ssid, WiFiReconnectionKind.Automatic, _password);
            Thread.Sleep(1000);
            if (result.ConnectionStatus == WiFiConnectionStatus.UnspecifiedFailure)
            {
                // Reset the network interface
                _wifi.Dispose();
                // Get the adapter
                _wifi = WiFiAdapter.FindAllAdapters()[_adapterNumber];
                // Get the network interface of the adapter
                _interface = NetworkInterface.GetAllNetworkInterfaces()[_wifi.NetworkInterface];
                ConnectionResult?.Invoke(false);
                return false;
            }
            else if (result.ConnectionStatus != WiFiConnectionStatus.Success)
            {
                Debug.WriteLine("Could not connect, WiFiConnectionStatus code: " + result.ConnectionStatus.ToString());
                ConnectionResult?.Invoke(false);
                return false;
            }

            // Enable DHCP
            _interface.EnableDhcp();

            // Wait up to 15 seconds for an assigned IP address
            string ip;
            int i = 0;
            do
            {
                Thread.Sleep(1000);
                ip = _interface.IPv4Address;
                i++;
            } while ((ip is null || ip == "0.0.0.0") && i < 15);

            if (ip is null || ip == "0.0.0.0")
            {
                Debug.WriteLine("Could not get IP address.");
                ConnectionResult?.Invoke(false);
                return false;
            }
            Debug.WriteLine("IP: " + ip);

            // Inform game server of bot and check response
            bool success =  SendToServerURL("/Bot/Index?ip=" + ip + "&name=" + RobotName) == "AK";
            ConnectionResult?.Invoke(success);
            return success;
        }

        /// <summary>
        /// Called when a message from the game server is received.
        /// </summary>
        /// <param name="message">The message received.</param>
        /// <param name="caller">The socket connection the message was received on.</param>
        private void MessageReceived(string message, Socket caller = null)
        {
            Debug.WriteLine("Message received: " + message);
            // Check if in setup mode
            if (_inSetupMode)
            {
                SetupMode(message, caller);
            }
            else
            {
                // Respond and close connection
                caller.Send(new byte[] { 0x4F, 0x4B }); // Send OK
                caller.Close();                

                // Check if game is already started
                if (_started)
                {
                    byte movement = 0;
                    byte magnitude = 0;
                    byte outOfTurn = 0;
                    // Parse movement instruction
                    try
                    {
                        movement = byte.Parse(message.Substring(0, 1));
                        magnitude = byte.Parse(message.Substring(1, 1));
                        outOfTurn = byte.Parse(message.Substring(2, 1));
                    }
                    catch
                    {
                        Debug.WriteLine("Bad message format");
                        return;
                    }
                    if (outOfTurn == 2)
                    {
                        // Bot received reset command
                        _started = false;
                        Reset?.Invoke(this, EventArgs.Empty);
                    }

                    else
                    {
                        // Bot received move order
                        ExecuteMove(movement, magnitude, outOfTurn);
                    }
                }
                else
                {
                    // Parse instruction, has the format instruction:message
                    int instruction = 0;
                    try
                    {
                        instruction = int.Parse(message.Substring(0, message.IndexOf(':')));
                    }
                    catch
                    {
                        Debug.WriteLine("Bad message format");
                        return;
                    }
                    // Bot has been assigned to player
                    if (instruction == 0)
                    {
                        // Parse message
                        message = message.Substring(message.IndexOf(':') + 1);
                        // Raise player assigned event
                        PlayerAssigned?.Invoke(int.Parse(message.Substring(0, 1)));
                        // Get assigned bot number
                        _botNumber = message.Substring(1);
                        _started = true;
                    }
                    else if (instruction == 1)
                    {
                        // Enter setup mode
                        _inSetupMode = true;
                        SetupModeState?.Invoke(false);

                    }
                }
            }
        }

        /// <summary>
        /// Parses and executes a move command.
        /// </summary>
        /// <param name="movement">The type of movement.</param>
        /// <param name="magnitude">The magnitude of the movement.</param>
        /// <param name="outOfTurn">If the robot is moving not on its turn.</param>
        private void ExecuteMove(byte movement, byte magnitude, byte outOfTurn)
        {
            if (movement <= 3)
            {
                // Standard movement
                if (magnitude > 0)
                {
                    switch (movement)
                    {
                        case 0:
                            // Left
                            Turn?.Invoke(magnitude, 1, outOfTurn);
                            break;
                        case 1:
                            // Right
                            Turn?.Invoke(magnitude, 0, outOfTurn);
                            break;
                        case 2:
                            // Forward
                            DriveForward?.Invoke(magnitude, outOfTurn);
                            break;
                        case 3:
                            // Backup
                            DriveBackward?.Invoke(magnitude, outOfTurn);
                            break;
                    }
                }
                else
                {
                    // Robot trying to move, but is blocked
                    BlockedMove?.Invoke(this, EventArgs.Empty);
                }
            }
            // Non-movement command
            else
            {
                switch (movement)
                {
                    case 4:
                        // Take damage
                        TakeDamage?.Invoke(magnitude);
                        break;
                }
            }
            // Inform server that the bot has finished moving
            SendToServerURL("/Bot/Done?bot=" + _botNumber);
        }

        /// <summary>
        /// Processes server commands while in setup mode.
        /// </summary>
        /// <param name="message">The message from the game server.</param>
        /// <param name="caller">The socket the message came in on.</param>
        private void SetupMode(string message, Socket caller)
        {
            // Parse instruction

            int instruction = 0;
            try
            {
                instruction = int.Parse(message.Substring(0, message.IndexOf(':')));
            }
            catch
            {
                Debug.WriteLine("Bad message format");
                caller.Close();
                return;
            }

            // Check if a response is needed here
            if (instruction != 0)
            {
                // Respond and close the connection
                caller.Send(new byte[] { 0x4F, 0x4B }); // Send OK
                caller.Close();

                // Parse the message
                message = message.Substring(message.IndexOf(':') + 1);
            }

            if (instruction == 0)
            {
                // Load the settings
                SettingsEventArgs settingsArgs = new SettingsEventArgs();
                GetSettings?.Invoke(settingsArgs);
                string settings = settingsArgs.Settings;

                // Send the settings to the game server
                caller.Send(Encoding.UTF8.GetBytes(settings));
                caller.Close();
            }
            else if (instruction == 1)
            {
                // Save the settings temporarily
                UpdateSettings?.Invoke(new SettingsEventArgs(message));
                // Run a speed test
                SpeedTest?.Invoke(this, EventArgs.Empty);
            }
            else if (instruction == 2)
            {
                // Save the settings temporarily
                UpdateSettings?.Invoke(new SettingsEventArgs(message));
                // Run a navigation test
                NavigationTest?.Invoke(this, EventArgs.Empty);
            }
            else if (instruction == 3)
            {
                // Save the settings persistently
                UpdateSettings?.Invoke(new SettingsEventArgs(message, true));
                // Exit setup mode
                SetupModeState?.Invoke(true);
                _inSetupMode = false;
            }
        }

        /// <summary>
        /// Launches a TCP listener on port 8080.
        /// </summary>
        public void ServerListen()
        {
            Debug.WriteLine("Starting listener");
            // Ensure socket exists
            if (_listener == null)
            {
                _listener = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
                _listener.SetSocketOption(SocketOptionLevel.Socket, SocketOptionName.ReuseAddress, true);
                _listener.Bind(new IPEndPoint(IPAddress.Any, 8080));
                _listener.Listen(1);
            }

            string message = "";
            try
            {
                // Wait for an incoming connection
                using (Socket handler = _listener.Accept())
                {
                    // Create buffers to receive data
                    byte[] buffer = new byte[128];
                    char[] charbuffer = new char[128];
                    // Create decoder to read data
                    Decoder d = Encoding.UTF8.GetDecoder();
                    bool converted;
                    int outbyte, outchar;
                    // Read all data on the socket
                    while (handler.Available > 0)
                    {
                        handler.Receive(buffer, 128, SocketFlags.None);
                        // Decode data received
                        d.Convert(buffer, 0, 128, charbuffer, 0, 128, true, out outbyte, out outchar, out converted);
                        // Add each character to the message string
                        foreach (char c in charbuffer)
                        {
                            message += c;
                        }
                    }
                    MessageReceived(message.Trim(), handler);
                    handler?.Close();
                }
            }
            catch (SocketException ex)
            {
                Debug.WriteLine("Socket exception: " + ex.ErrorCode.ToString());
                if (ex.ErrorCode == (int)SocketError.WouldBlock)
                {
                    _listener?.Close();
                    _listener = null;
                    GC.WaitForPendingFinalizers();
                }
            }
            catch (Exception ex)
            {
                Debug.WriteLine("Server error: " + ex.Message);
            }
            // Send received message to be processed
        }

        /// <summary>
        /// Sends a GET request to the game server.
        /// </summary>
        /// <param name="message">The URL path and GET parameters to send.</param>
        /// <returns>The response from the game server or an empty string on failure.</returns>
        private string SendToServerURL(string message)
        {
            string request = "GET " + message + " HTTP/1.1\r\nHost: " + _serverAddress + ":" + _port + "\r\nConnection: close\r\n\r\n";
            Socket connection = null;
            try
            {
                connection = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
            } 
            catch (SocketException ex)
            {
                Debug.WriteLine("Error creating request socket: " + ex.ErrorCode.ToString());
                return "";
            }
            
            EndPoint ep = new IPEndPoint(IPAddress.Parse(_serverAddress), int.Parse(_port));
            string response = "";
            try
            {
                // Create connection and send message
                connection.Connect(ep);
                connection.Send(Encoding.UTF8.GetBytes(request));
                // Create buffers to receive data
                byte[] buffer = new byte[128];
                char[] charbuffer = new char[128];
                // Create decoder to read data
                Decoder d = Encoding.UTF8.GetDecoder();
                bool converted;
                int outbyte, outchar;
                // Read all data from the response
                Thread.Sleep(10);
                while (connection.Receive(buffer, 0, 128, SocketFlags.None) > 0)
                {
                    // Decode data received
                    d.Convert(buffer, 0, 128, charbuffer, 0, 128, true, out outbyte, out outchar, out converted);
                    // Add each character to the message string
                    foreach (char c in charbuffer)
                    {
                        response += c;
                    }
                    // Reset buffers
                    buffer = new byte[128];
                    charbuffer = new char[128];
                }
            }
            catch(Exception ex)
            {
                Debug.WriteLine("Error connecting to game server: " + ex.Message);
            }

            // Close the connection
            connection.Close();

            // Extract response body
            int body = response.IndexOf("\r\n\r\n");
            if (body != -1)
            {
                response = response.Substring(body + 4).Trim();
            }
            else
            {
                Debug.WriteLine("Bad sever response: " + response);
                response = "";
            }
            return response;
        }      
    }

    /// <summary>
    /// Custom event arguments for retrieving or updating robot settings.
    /// </summary>
    public class SettingsEventArgs : EventArgs
    {
        /// <summary>
        /// Creates a new settings event arguments object.
        /// </summary>
        /// <param name="settings">The settings to update, if updating.</param>
        /// <param name="commit">If updating, commit settings to persistent storage.</param>
        public SettingsEventArgs(string settings = "", bool commit = false)
        {
            Settings = settings;
            Commit = commit;
        }

        /// <summary>
        /// The robot settings to retrieve or write to.
        /// </summary>
        public string Settings { get; set; }

        /// <summary>
        /// If updating the settings, commit them to persistent storage
        /// </summary>
        public bool Commit { get; }
    }
}