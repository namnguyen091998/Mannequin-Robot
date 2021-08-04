#include <Wire.h>
#include <AccelStepper.h>
#include <MultiStepper.h>
#include "Receive_data.h"
//Defind Right Hand
//#define EnPinRight 37
#define DirPinRight 39
#define StepPinRight 41
//Define Left Hand
//#define EnPinLeft 31
#define DirPinLeft 4//33
#define StepPinLeft 3//35
//Define Head
#define EnPinHead 43
#define DirPinHead 45
#define StepPinHead 47

//Defind homing/limit switches
#define StopperPinLeft 8 //51
#define StopperPinRight 53

char receivedCommand;

bool beginLeft = false;
bool beginRight = false;
bool checkHomeLeft = false;
bool checkHomeRight = false;


const float resolution = 200.0;


int step_degree(float desired_degree){
  return (desired_degree/(360.0/resolution));
}

MultiStepper hand_control;
AccelStepper stepperLeft = AccelStepper(AccelStepper::DRIVER, StepPinLeft, DirPinLeft);
AccelStepper stepperRight = AccelStepper(AccelStepper::DRIVER, StepPinRight, DirPinRight);
AccelStepper stepperHead = AccelStepper(AccelStepper::DRIVER, StepPinHead, DirPinHead);



void setStepperLeft() {
	stepperLeft.setMaxSpeed(100.0);
	stepperLeft.setAcceleration(50.0);
}
void setStepperRight() {
	stepperRight.setMaxSpeed(100.0);
	stepperRight.setAcceleration(50.0);
}

void setLimitSwitches(){
  pinMode(StopperPinLeft, INPUT_PULLUP);
  pinMode(StopperPinRight, INPUT_PULLUP);
}


void setup() {
  Serial.begin(57600);
  setLimitSwitches();
  setStepperLeft();
  setStepperRight();
  stepperRight.disableOutputs();
  stepperLeft.disableOutputs();
}

void loop() {
  StartLeft();
  StartRight();
  if(beginLeft == true && beginRight == true){
    recvWithStartEndMarkers();
    if(degree > 1){
      setStepperLeft();
      stepperLeft.moveTo(step_degree(degree));
      checkHomeLeft = true;
      degree = 0;
    }
    controlLeftHand();
    controlRightHand();
  }
}
bool isHomeLeft() {
  bool stopperLeft = digitalRead(StopperPinLeft);
  return stopperLeft;
}

bool isHomeRight() {
  bool stopperRight = digitalRead(StopperPinRight);
  return stopperRight;
}
void controlLeftHand(){
  if(checkHomeLeft == true)
  {
    if (stepperLeft.distanceToGo() == 0){
      beginLeft = false;
      delay(2000);
    }
    stepperLeft.enableOutputs();
    stepperLeft.run();
  } 
}
void controlRightHand(){
  if(checkHomeRight == true)
  {
    if (stepperRight.distanceToGo() == 0){
      beginRight = false;
      delay(2000);
    }
    stepperRight.enableOutputs();
    stepperRight.run();
  }
}
void returnHomeRight(){
  if(!isHomeRight()){
    stepperRight.setCurrentPosition(0);
    stepperRight.stop(); //stop motor
    stepperRight.disableOutputs(); //disable power
    beginRight = true;
    checkHomeRight = false;
    Serial.println("Right hand is homing");
    return;
  }
  setStepperRight();
  stepperRight.moveTo(-1*1000000);
  stepperRight.run();
}
void returnHomeLeft(){
  if(!isHomeLeft()){
    stepperLeft.setCurrentPosition(0);
    stepperLeft.stop(); //stop motor
    stepperLeft.disableOutputs(); //disable power
    beginLeft = true;
    checkHomeLeft = false;
    Serial.println("Left hand is homing");
    return;
  }
  setStepperLeft();
  stepperLeft.moveTo(-1*1000000);
  stepperLeft.run();
}
void StartLeft(){
  if(beginLeft == false){
    returnHomeLeft();
    return;
  }
}
void StartRight(){
  if(beginRight == false){
    returnHomeRight();
    return;
  }
}
