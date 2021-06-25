const byte numChars = 32;
char receive_buffer[numChars];
char *pointer_chr;
float angular_vel,linear_vel;
float angular_vel_cons,linear_vel_cons;
int step_position;
String transmission = "";
boolean newData = false;

void setup() {
    Serial.begin(57600);
    Serial.println("<Arduino is ready>");
}

void loop() {
    recvWithStartEndMarkers();
}

void recvWithStartEndMarkers() {
    static boolean recvInProgress = false;
    char startMarker = '<';
    char endMarker = '>';
    static byte ndx = 0;   
    while (Serial.available() > 0 && newData == false) {
        char rc = Serial.read();     
        if (recvInProgress == true) {
            if (rc != endMarker) {
                receive_buffer[ndx] = rc;
                transmission += rc;
                ndx++;
                if (ndx >= numChars) {
                    ndx = numChars - 1;
                } 
            }
            else {
                receive_buffer[ndx] = '\0'; // terminate the string
                recvInProgress = false;
                ndx = 0;
                newData = true;
                showNewData();
            }
        }

        else if (rc == startMarker) {
            recvInProgress = true;
    }
  }
}

void showNewData() {
  if(newData == true)  {
    Serial.println(transmission);
    int firstColon = transmission.indexOf(":");
    int secondColon = transmission.indexOf(':',firstColon+1);
    int firstSpace = transmission.indexOf(" ");
    int thirdColon = transmission.indexOf(':',secondColon+1);
    int secondSpace = transmission.indexOf(" ", firstSpace+1);
    if(transmission.substring(0,firstColon) == "angular"){
      char cmdValue[10];
      pointer_chr = receive_buffer;
      strncpy(cmdValue, pointer_chr + firstColon + 1,firstSpace - (firstColon+1));
      angular_vel = atof(cmdValue);
      angular_vel_cons = constrain(angular_vel, -100.0, 100.0);
      Serial.println(angular_vel_cons);
     }
   if(transmission.substring(firstSpace+1,secondColon) == "linear"){
      char cmdValue[10];
      pointer_chr = receive_buffer;
      strncpy(cmdValue, pointer_chr + secondColon + 1,secondSpace - 1 - secondColon );
      linear_vel = atof(cmdValue);
      linear_vel_cons = constrain(linear_vel, -100.0, 100.0);
      Serial.println(linear_vel_cons);
    }
    if(transmission.substring(secondSpace+1,thirdColon) == "step"){
      char cmdValue[10];
      pointer_chr = receive_buffer;
      strncpy(cmdValue, pointer_chr + thirdColon + 1,transmission.length() - 1 - thirdColon );
      step_position = atoi(cmdValue);
      Serial.println(step_position);
    }
    newData = false;
    transmission = "";
  }
}
