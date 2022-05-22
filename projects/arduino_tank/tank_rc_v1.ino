// -------
// IO Pins
// -------
// L = REVERSE
// R = FORWARD

#define PPM_DATA_PIN 2
#define L_EN 3
#define R_EN 4
#define L_PWM 5
#define R_PWM 6
#define L_IS 7
#define R_IS 8

// --------------
// Radio Settings
// --------------

/*
  Each PPM frame can be of variable length, depending on the values of each
  channel. The start of a frame is indicated with a high state that lasts over
  2ms (2000μs). The delay between channel pulses is typically 300μs, and each
  channel pulse is normally between 700-1700μs, to give a channel range of
  1000-2000.
*/


#define RX_STRAIGHT_CHANNEL 2
#define RX_TURN_CHANNEL 1
#define MIN_SIGNAL 1000
#define MAX_SIGNAL 2000
#define RX_CHANNEL_COUNT 8
#define RX_DEADZONE 7
#define RX_INITIAL_VALUE 1500
#define SIGNAL_METHOD FALLING
#define START_FRAME_LENGTH 2100
#define MAX_SPEED 255
#define TIMEOUT_DELAY 1000

// -----------------
// Serial Monitoring
// -----------------

#define BAUD_RATE 115200

// -----------
// Code Begins
// -----------

/*
  We need one additional "channel" that will be used to capture the start frame
  along with any delay between PPM frames. Channel 0 is used, which handily
  makes all the channels correspond with their array index value.
*/
int rx_channel_data[RX_CHANNEL_COUNT + 1];

// Allow main loop to detect lost signal, and pause motors
unsigned long int last_signal_received_at = 0;
int left_motor_speed = 0;
int right_motor_speed = 0;

void setup()
{
  // Zero RX Channel Data
  for (int i = 0; i <= RX_CHANNEL_COUNT; i++)
  {
    rx_channel_data[i] = RX_INITIAL_VALUE;
  }
  Serial.begin(BAUD_RATE);

  // Setup pin modes
  // pinMode(L_IS, INPUT);
  // pinMode(R_IS, INPUT);
  pinMode(L_EN, OUTPUT);
  pinMode(R_EN, OUTPUT);
  pinMode(L_PWM, OUTPUT);
  pinMode(R_PWM, OUTPUT);

  // Zero everything out
  disableMotors();

  last_signal_received_at = micros();

  // Attach interrupt to PPM pin
  attachInterrupt(
    digitalPinToInterrupt(PPM_DATA_PIN),
    ppm_interrupt,
    SIGNAL_METHOD
  );

  // Let it sit for a second before starting
  delay(1000);
}

int speed = 0;

void loop()
{
  // if((micros() - last_signal_received_at) > TIMEOUT_DELAY)
  // {
  //   disableMotors();
  //   delay(25);
  // } else {
  //   calculateMotorSpeeds();
  //   setMotorSpeeds();
  // }
  calculateMotorSpeeds();
  setMotorSpeeds();
}

int ppm_to_speed(int ppm_value) {
  int speed = map(ppm_value, 1000, 2000, -MAX_SPEED, MAX_SPEED);
  speed = constrain(speed, -MAX_SPEED, MAX_SPEED);
  return speed;
}

void calculateMotorSpeeds() {
  // Reset to 0
  left_motor_speed = 0;
  right_motor_speed = 0;
  // Name channels
  int straight_channel = rx_channel_data[RX_STRAIGHT_CHANNEL];
  int turn_channel = rx_channel_data[RX_TURN_CHANNEL];
  // Forward/Backward
  if(abs(straight_channel - 1500) > RX_DEADZONE) {
    left_motor_speed = ppm_to_speed(straight_channel);
    right_motor_speed = ppm_to_speed(straight_channel);
  }
  // Left/Right
  if(abs(turn_channel - 1500) > RX_DEADZONE) {
    left_motor_speed += ppm_to_speed(turn_channel);
    right_motor_speed -= ppm_to_speed(turn_channel);
  }
  // Contrain motors to max speed when mixing
  left_motor_speed = constrain(left_motor_speed, -MAX_SPEED, MAX_SPEED);
  right_motor_speed = constrain(right_motor_speed, -MAX_SPEED, MAX_SPEED);
}

void stopLeftMotor() {
  digitalWrite(L_EN, LOW);
  analogWrite(L_PWM, 0);
}

void stopRightMotor() {
  digitalWrite(R_EN, LOW);
  analogWrite(R_PWM, 0);
}

void disableMotors() {
  left_motor_speed = 0;
  right_motor_speed = 0;
  setMotorSpeeds();
}

void setMotorSpeeds() {
  if(left_motor_speed > 0) {
    digitalWrite(L_EN, HIGH);
    analogWrite(L_PWM, left_motor_speed);
  } else if (left_motor_speed < 0) {
    digitalWrite(L_EN, LOW);
    analogWrite(L_PWM, abs(left_motor_speed));
  } else {
    stopLeftMotor();
  }

  if(right_motor_speed > 0) {
    digitalWrite(R_EN, HIGH);
    analogWrite(R_PWM, right_motor_speed);
  } else if (right_motor_speed < 0) {
    digitalWrite(R_EN, LOW);
    analogWrite(R_PWM, abs(right_motor_speed));
  } else {
    stopRightMotor();
  }
}

void write_ppm_to_serial()
{
  Serial.print(rx_channel_data[0]);
  Serial.print("\t");
  for (byte i = 1; i <= RX_CHANNEL_COUNT; i++)
  {
    int parsed_output = constrain(rx_channel_data[i], MIN_SIGNAL, MAX_SIGNAL) - MIN_SIGNAL;
    Serial.print(parsed_output);
    Serial.print("\t");
  }
  Serial.print("\n");
}

void ppm_interrupt()
{
  // TODO: Find efficient way to wait for start frame before running loop
  static byte current_channel = 0;
  // Fake shortest expected signal length for initial value
  static unsigned long int previous_time = micros() - 1000;
  unsigned long int current_time = micros();
  unsigned long int delta_time = current_time - previous_time;
  previous_time = current_time;
  last_signal_received_at = current_time;

  if ((delta_time > START_FRAME_LENGTH) || (current_channel > RX_CHANNEL_COUNT))
  {
    current_channel = 0;
  }
  rx_channel_data[current_channel] = delta_time;
  current_channel++;
}
