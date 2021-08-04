// Include library of Arduino
//#include <ros.h>
//#include <geometry_msgs/Twist.h>
#include <FlexiTimer2.h>
#include <digitalWriteFast.h>
#include "Receive_data.h"
#include <math.h>


/*******************************************************************************
* Right motor config
*******************************************************************************/
// Encoder Pin
#define codeurPinA1 20
#define codeurPinB1 21
volatile long ticksCodeur1 = 0;
// Motor Pin
#define directionMoteur_1a  12
#define directionMoteur_1b  11
#define pwmMoteur_1  13

// Data sending rate in ms
#define TSDATA 100
unsigned long tempsDernierEnvoi = 0;
unsigned long tempsCourant = 0;
 
// Sampling rate in ms
#define CADENCE_MS1 10
volatile double dt1 = CADENCE_MS1/1000.;
volatile double temps1 = -CADENCE_MS1/1000.;
 
volatile double omega1;
volatile double commande1 = 0.;
float vref1;

 
// PID
volatile double Kp1 = 0.29;
volatile double Ki1 = 8.93;
volatile double P_x1 = 0.;
volatile double I_x1 = 0.;
volatile double ecart1 = 0.;


/*******************************************************************************
* Left motor config
*******************************************************************************/
//Encoder pin
#define codeurPinA2 2
#define codeurPinB2 3
volatile long ticksCodeur2 = 0;
// Motor pin
#define directionMoteur_2a  10
#define directionMoteur_2b  9
#define pwmMoteur_2  8

// Sampling rate in ms
#define CADENCE_MS2 10
volatile double dt2 = CADENCE_MS2/1000.;
volatile double temps2 = -CADENCE_MS2/1000.;
 
volatile double omega2;
volatile double commande2 = 0.;
float vref2;

// PID
volatile double Kp2 = 0.29;
volatile double Ki2 = 8.93;
volatile double P_x2 = 0.;
volatile double I_x2 = 0.;
volatile double ecart2 = 0.;
float vel_l,vel_a;


//ros::NodeHandle nh;
//void controlDirect(const geometry_msgs::Twist& cmd_vel_msg);
//ros::Subscriber<geometry_msgs::Twist> cmd_vel_sub("cmd_vel", controlDirect);
#define R 0.0325
void controlDirect(float linear_vel, float angular_vel); 
void setup(){
    Serial.begin(9600);
 // nh.initNode();
    pinMode(codeurPinA1, INPUT);      // digital input pin A1 encoder
    pinMode(codeurPinB1, INPUT);      // digital input pin B1 encoder
    pinMode(codeurPinA2, INPUT);      // digital input pin A2 encoder
    pinMode(codeurPinB2, INPUT);      // digital input pin B2 encoder
    digitalWrite(codeurPinA1, HIGH);  // activate the pull up resistor
    digitalWrite(codeurPinB1, HIGH);  // activate the pull up resistor
    digitalWrite(codeurPinA2, HIGH);  // activate the pull up resistor
    digitalWrite(codeurPinB2, HIGH);  // activate the pull up resistor
  
    attachInterrupt(3, GestionInterruptioncodeurPinA1, CHANGE); //interrupt
    attachInterrupt(2, GestionInterruptioncodeurPinB1, CHANGE); //interrupt
    attachInterrupt(1, GestionInterruptioncodeurPinA2, CHANGE); //interrupt
    attachInterrupt(0, GestionInterruptioncodeurPinB2, CHANGE); //interrupt 
    
    // Motor Pin 
    pinMode(directionMoteur_1a, OUTPUT);
    pinMode(directionMoteur_1b, OUTPUT);
    pinMode(pwmMoteur_1, OUTPUT);
    pinMode(directionMoteur_2a, OUTPUT);
    pinMode(directionMoteur_2b, OUTPUT);
    pinMode(pwmMoteur_2, OUTPUT);
    
    // The isrt routine is executed at a fixed rate
    FlexiTimer2::set(CADENCE_MS1, 1/1000., isrt1); //timer resolution = 1 ms
    FlexiTimer2::start();
 //   nh.subscribe(cmd_vel_sub);
  }
  
 void loop(){
   recvWithStartEndMarkers();
   controlDirect(linear_vel_cons,angular_vel_cons);
//   Serial.print("Velocity_Right:");
//   Serial.print(omega1);
//   Serial.print(" , ");
//   Serial.print("Velocity_Left:");
//   Serial.print(omega2);
//   Serial.print(" , ");
//   Serial.print("Error_Right:");
//   Serial.print(ecart1);
//   Serial.print(" , ");
//   Serial.print("Error_left:");
//   Serial.println(ecart2);
}
  //PID velocity
void isrt1(){
 
  int codeurDeltaPos1;
  int codeurDeltaPos2;
  double tensionBatterie1;
  double tensionBatterie2;
  
  // Number of encoder ticks since the last time
  codeurDeltaPos2 = ticksCodeur2;
  codeurDeltaPos1 = ticksCodeur1;

  
  ticksCodeur1 = 0;
  ticksCodeur2 = 0;
  
  // Calculate the rotation speed
  omega1 = ((2.*3.141592*((double)codeurDeltaPos1))/2160.)/dt1;  // en rad/s
  omega2 = ((2.*3.141592*((double)codeurDeltaPos2))/2160.)/dt2;  // en rad/s
  //******* PID regulation ******** //
  // Difference between the reference and the measurement
  ecart1 = vref1 - omega1;
  ecart2 = vref2 - omega2;

  // Proportional term
  P_x1 = Kp1 * ecart1;
  P_x2 = Kp2 * ecart2;
  
  // Calculate the order
  commande1 = P_x1 + I_x1;
  commande2 = P_x2 + I_x2;

  // Integral term (will be used during the next sampling step)
  I_x1 = I_x1 + Ki1 * dt1 * ecart1;
  I_x2 = I_x2 + Ki2 * dt2 * ecart2;
  
  /******* End of PID regulation ********/
 
   // Send the command to the motor
  tensionBatterie1 = 12;
  tensionBatterie2 = 12;
   int tension_int1;
 
    // Normalization of the supply voltage in relation to the battery voltage
    tension_int1 = (int)(255*(commande1/tensionBatterie1));
 
    // Saturation for safety
    if (tension_int1>255) {
        tension_int1 = 255;
    }
    if (tension_int1<-255) {
        tension_int1 = -255;
    }
    int tension_int2;
    // Normalization of the supply voltage in relation to the battery voltage
    tension_int2 = (int)(255*(commande2/tensionBatterie2));
 
    // Saturation for safety
    if (tension_int2>255) {
        tension_int2 = 255;
    }
    if (tension_int2<-255) {
        tension_int2 = -255;
    }
  controlMotor(1, tension_int1);
  controlMotor(2, tension_int2);
}
//control motor 1
void controlMotor(int motor,double tension_int)
{
  if(motor == 1){
    if(tension_int > 0){ //forward
      digitalWrite(directionMoteur_1a, LOW);//in1
      digitalWrite(directionMoteur_1b, HIGH);//in2
      analogWrite(pwmMoteur_1, tension_int);
    }
    else if(tension_int < 0){ //backward
      digitalWrite(directionMoteur_1a, HIGH);//in1
      digitalWrite(directionMoteur_1b, LOW);//in2
      analogWrite(pwmMoteur_1, -tension_int);
    }
    else{
      digitalWrite(directionMoteur_1a, LOW);//in1
      digitalWrite(directionMoteur_1b, LOW);//in2
    }
  }
  if(motor ==2){
    if(tension_int > 0){
      digitalWrite(directionMoteur_2a, LOW);//in1
      digitalWrite(directionMoteur_2b, HIGH);//in2
      analogWrite(pwmMoteur_2, tension_int);
    }
    else if(tension_int < 0){
      digitalWrite(directionMoteur_2a, HIGH);//in1
      digitalWrite(directionMoteur_2b, LOW);//in2
      analogWrite(pwmMoteur_2, -tension_int); 
    }
    else{
      digitalWrite(directionMoteur_2a, LOW);//in1
      digitalWrite(directionMoteur_2b, LOW);//in2
    }
  }
}


void controlDirect(float linear_vel, float angular_vel){
  linear_vel = constrain(linear_vel, -0.22, 0.22);
  angular_vel = constrain(angular_vel, -2.0, 2.0);
  if(angular_vel == 0){
        vref1 = linear_vel/R;
        vref2 = vref1; // forward
  }
  else if(linear_vel == 0){
    vref1 = angular_vel;
    vref2 = -vref1; //rotation
  }
  else{
    vref1 = (linear_vel/R + angular_vel); //10 : distance between 2 wheels
    vref2 = (linear_vel/R - angular_vel);
  }
}

// Read encoder Right motor
void GestionInterruptioncodeurPinA1()
{
   if (digitalReadFast2(codeurPinA1) != digitalReadFast2(codeurPinB1)) {
    ticksCodeur1++;
  }
  else {
    ticksCodeur1--;
  }
}
void GestionInterruptioncodeurPinB1()
{
   if (digitalReadFast2(codeurPinA1) != digitalReadFast2(codeurPinB1)) {
    ticksCodeur1--;
  }
  else {
    ticksCodeur1++;
  }
}

 
// Read encoder Left motor

void GestionInterruptioncodeurPinA2()
{
   if (digitalReadFast2(codeurPinA2) != digitalReadFast2(codeurPinB2)) {
    ticksCodeur2++;
  }
  else {
    ticksCodeur2--;
  }
}
void GestionInterruptioncodeurPinB2()
{
   if (digitalReadFast2(codeurPinA2) != digitalReadFast2(codeurPinB2)) {
    ticksCodeur2--;
  }
  else {
    ticksCodeur2++;
  }
}
