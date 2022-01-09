using System;
using System.Device.I2c;
using System.Diagnostics;
using System.Threading;

namespace RingbitCar
{
    /// <summary>
    /// Class for communicating with the MPU6050 gyroscope/accelerometer.
    /// 
    /// Based largely on tockn's work:
    /// https://github.com/Tockn/MPU6050_tockn
    /// 
    /// Contributors: Sam Groveman
    /// </summary>
    class MPU6050
    {
        /// <summary>
        /// Total gyroscope measurement range in degrees/sec
        /// </summary>
        public enum GyroRange
        {
            TwoFifty = 0x00,
            FiveHundred = 0x08,
            OneThousand = 0x10,
            TwoThousand = 0x18
        }

        /// <summary>
        /// Total accelerometer range in g
        /// </summary>
        public enum AccelRange
        {
            Two = 0x00,
            Four = 0x08,
            Eight = 0x10,
            Sixteen = 0x18
        }

        private readonly I2cDevice _mpu6050;

        // Variables for calculating measurements
        private float gyroXoffset = 0, gyroYoffset = 0, gyroZoffset = 0;
        private float gyroSensitivity;
        private float accelSensitivity;

        // Variables for calculating total degrees
        private long _startTime;
        private float _totalXDegrees = 0, _totalYDegrees = 0, _totalZDegrees = 0;

        /// <summary>
        /// Register map
        /// </summary>
        private enum register
        {
            SMPLRT_DIV = 0x19,
            CONFIG = 0x1A,
            GYRO_CONFIG = 0x1B,
            ACCEL_CONFIG = 0x1C,
            PWR_MGMT_1 = 0x6B,
            TEMP_OUT = 0x41,
            GYRO_OUT = 0x43,
            ACCEL_OUT = 0x3B,

        }

        /// <summary>
        /// Creates an MPU6050 device class.
        /// 
        /// Appropriate I2C pins should already be configured.
        /// </summary>
        /// <param name="i2cbus">The bus the device is connected to</param>
        /// <param name="address">The address of the device</param>
        /// <param name="gyroConfig">The gyro range to use</param>
        /// <param name="accelConfig">The accelerometer range to use</param>
        public MPU6050(int i2cbus = 1, int address = 0x68, GyroRange gyroConfig = GyroRange.TwoFifty, AccelRange accelConfig = AccelRange.Two)
        {
            // Create the device
            _mpu6050 = I2cDevice.Create(new I2cConnectionSettings(i2cbus, address));

            // Reset the device
            write(register.PWR_MGMT_1, 0x80);
            Thread.Sleep(150);
            // Set the internal clock to use gyroscope Y
            write(register.PWR_MGMT_1, 0x02);
            // Configure measurement scales
            write(register.GYRO_CONFIG, (byte)gyroConfig);
            write(register.ACCEL_CONFIG, (byte)accelConfig);

            // Set sensitivity values
            switch (gyroConfig)
            {
                case GyroRange.TwoFifty:
                    gyroSensitivity = 131f;
                    break;
                case GyroRange.FiveHundred:
                    gyroSensitivity = 65.5f;
                    break;
                case GyroRange.OneThousand:
                    gyroSensitivity = 32.8f;
                    break;
                case GyroRange.TwoThousand:
                    gyroSensitivity = 16.4f;
                    break;
            }
            switch (accelConfig)
            {
                case AccelRange.Two:
                    accelSensitivity = 16384f;
                    break;
                case AccelRange.Four:
                    accelSensitivity = 8192f;
                    break;
                case AccelRange.Eight:
                    accelSensitivity = 4096f;
                    break;
                case AccelRange.Sixteen:
                    accelSensitivity = 2048f;
                    break;
            }
        }

        /// <summary>
        /// Calibrates the gyro by calculating offsets.
        /// It's very important to keep the device still during
        /// this process.
        /// </summary>
        /// <exception cref="SystemException">Thrown if there is an error retrieving measurement data.</exception>
        /// <returns>An array wit the X, Y, and Z offsets.</returns>
        public float[] calcGyroOffsets()
        {
            float x = 0, y = 0, z = 0;
            short rx, ry, rz;
            SpanByte result;

            Debug.WriteLine("Calculating gyro offsets.");
            Debug.WriteLine("DO NOT MOVE MPU6050!");
            Thread.Sleep(2000);

            // Take 3000 measurements
            for (int i = 0; i < 3000; i++)
            {
                result = read(register.GYRO_OUT, 6);

                if (result.IsEmpty)
                    throw new SystemException("Error getting calibration reading.");

                // Convert to 16 bit number
                rx = (short)(result[0] << 8 | result[1]);
                ry = (short)(result[2] << 8 | result[3]);
                rz = (short)(result[4] << 8 | result[5]);

                // Convert to deg/s
                x += rx / gyroSensitivity;
                y += ry / gyroSensitivity;
                z += rz / gyroSensitivity;
            }

            // Average and store measured values
            gyroXoffset = x / 3000;
            gyroYoffset = y / 3000;
            gyroZoffset = z / 3000;

            Debug.WriteLine("Done!");
            Debug.WriteLine("x: " + gyroXoffset.ToString());
            Debug.WriteLine("y: " + gyroYoffset.ToString());
            Debug.WriteLine("z: " + gyroZoffset.ToString());

            return new float[] { gyroXoffset, gyroYoffset, gyroZoffset };
        }


        /// <summary>
        /// Applies previously calculated gyro offsets.
        /// </summary>
        /// <param name="x">X offset value.</param>
        /// <param name="y">Y offset value.</param>
        /// <param name="z">Z offset value.</param>
        /// <returns>The values provided.</returns>
        public float[] calcGyroOffsets(float x, float y, float z)
        {
            gyroXoffset = x;
            gyroYoffset = y;
            gyroZoffset = z;

            return new float[] { x, y, z };
        }

        /// <summary>
        /// Get the current gyroscope reading.
        /// </summary>
        /// <returns>A float array with x, y, z gyroscope values.</returns>
        /// <exception cref="SystemException">Thrown if there is an error retrieving measurement data.</exception>
        public float[] getGyro()
        {
            float[] output = new float[3];
            SpanByte result = read(register.GYRO_OUT, 6);

            if (result.IsEmpty)
                throw new SystemException("Error getting gyro reading.");

            // Convert to 16 bit number
            short rawX = (short)(result[0] << 8 | result[1]);
            short rawY = (short)(result[2] << 8 | result[3]);
            short rawZ = (short)(result[4] << 8 | result[5]);

            // Convert to deg/s subtracting offset value
            output[0] = (rawX / gyroSensitivity) - gyroXoffset;
            output[1] = (rawY / gyroSensitivity) - gyroYoffset;
            output[2] = (rawZ / gyroSensitivity) - gyroZoffset;

            return output;
        }

        /// <summary>
        /// Get the current accelerometer reading.
        /// </summary>
        /// <returns>A float array with x, y, z accelerometer values.</returns>
        /// <exception cref="SystemException">Thrown if there is an error retrieving measurement data.</exception>
        public float[] getAccel()
        {
            float[] output = new float[3];
            SpanByte result = read(register.ACCEL_OUT, 6);


            if (result.IsEmpty)
                throw new SystemException("Error getting accelerometer reading.");

            // Convert to 16 bit number
            short rawX = (short)(result[0] << 8 | result[1]);
            short rawY = (short)(result[2] << 8 | result[3]);
            short rawZ = (short)(result[4] << 8 | result[5]);

            // Convert to g
            output[0] = (rawX / accelSensitivity);
            output[1] = (rawY / accelSensitivity);
            output[2] = (rawZ / accelSensitivity);

            return output;
        }

        /// <summary>
        /// Get the current temperature reading.
        /// </summary>
        /// <returns>Degrees C</returns>
        /// <exception cref="SystemException">Thrown if there is an error retrieving measurement data.</exception>
        public float getTemp()
        {
            SpanByte result = read(register.TEMP_OUT, 2);

            if (result.IsEmpty)
                throw new SystemException("Error getting temperature reading.");

            // Convert to 16 bit number
            short rawTemp = (short)(result[0] << 8 | result[1]);

            // Calculate deg C
            float temperature = rawTemp / 340.0f + 36.53f;

            return temperature;
        }

        /// <summary>
        /// Gets the total number of degrees rotated since the
        /// start of the interval timer.
        /// </summary>
        /// <returns>A float array with x, y, z total degree values</returns>
        public float[] getGyroDegrees()
        {
            // Get the gyro readings
            float[] values = getGyro();
            // Get the time passed since last measured in seconds
            float interval = ((DateTime.UtcNow.Ticks - _startTime) / TimeSpan.TicksPerMillisecond) * 0.001f;
            // Reset the starting time
            _startTime = DateTime.UtcNow.Ticks;

            // Add the degrees rotated since last measured to the total
            _totalXDegrees += values[0] * interval;
            _totalYDegrees += values[1] * interval;
            _totalZDegrees += values[2] * interval;

            return new float[] { _totalXDegrees, _totalYDegrees, _totalZDegrees };
        }

        /// <summary>
        /// Resets all the values used for calculating <see cref="getGyroDegrees"/>.
        /// </summary>
        public void ResetGyroDegrees()
        {
            _startTime = DateTime.UtcNow.Ticks;
            _totalXDegrees = 0;
            _totalYDegrees = 0;
            _totalZDegrees = 0;
        }

        /// <summary>
        /// Write data to a register on the device.
        /// </summary>
        /// <param name="address">The register address.</param>
        /// <param name="data">The data to write.</param>
        /// <returns>True on a successful write.</returns>
        private bool write(register address, byte data)
        {
            SpanByte transmission = new SpanByte(new byte[] { (byte)address, data });
            I2cTransferResult result = _mpu6050.Write(transmission);
            if (result.Status == I2cTransferStatus.FullTransfer)
            {
                return true;
            }
            return false;
        }

        /// <summary>
        /// Reads data from a register on the device.
        /// </summary>
        /// <param name="address">The register address.</param>
        /// <param name="buffersize">The number of bytes of data to read.</param>
        /// <returns>The bytes received or an empty SpanByte on failure.</returns>
        private SpanByte read(register address, int buffersize)
        {
            SpanByte transmission = new SpanByte(new byte[] { (byte)address });
            SpanByte received = new SpanByte(new byte[buffersize]);
            I2cTransferResult result = _mpu6050.WriteRead(transmission, received);
            if (result.Status == I2cTransferStatus.FullTransfer)
            {
                return received;
            }
            return new SpanByte();
        }
    } 
}
