// Define pins
#define L_EN 3
#define R_EN 4
#define L_PWM 5
#define R_PWM 6
#define L_IS 7
#define R_IS 8

// L = REVERSE
// R = FORWARD

void setup()
{
  // Setup pin modes
  pinMode(L_IS, INPUT);
  pinMode(R_IS, INPUT);
  pinMode(L_EN, OUTPUT);
  pinMode(R_EN, OUTPUT);
  pinMode(L_PWM, OUTPUT);
  pinMode(R_PWM, OUTPUT);

  // Zero everything out
  disableMotors();

  // Let it sit for a second before starting
  delay(1000);
}

int speed = 0;

void loop()
{
  enableRightMotor();
  for(speed = 0; speed <= 255; speed++) {
    analogWrite(L_PWM, 0);
    analogWrite(R_PWM, speed);
    delay(20);
  }
  disableMotors();

  delay(500);

  enableLeftMotor();
  for(speed = 0; speed <= 255; speed++) {
    analogWrite(L_PWM, speed);
    analogWrite(R_PWM, 0);
    delay(20);
  }
  disableMotors();

  delay(500);
}

void zeroSpeed() {
  analogWrite(L_PWM, 0);
  analogWrite(R_PWM, 0);
}

void disableMotors() {
  digitalWrite(L_EN, LOW);
  digitalWrite(R_EN, LOW);
  zeroSpeed();
}

void enableLeftMotor() {
  digitalWrite(L_EN, HIGH);
  digitalWrite(R_EN, LOW);
  zeroSpeed();
}

void enableRightMotor() {
  digitalWrite(L_EN, LOW);
  digitalWrite(R_EN, HIGH);
  zeroSpeed();
}
