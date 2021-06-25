import serial # Module needed for serial communication
import time # Module needed to add delays in the code

ser = serial.Serial('/dev/ttyACM0', 57600, timeout=.0000001)

# Get rid of garbage/incomplete data
ser.flush()
step_angle = 0
angular = 0
linear = 0
# Infinite loop
while (1):

  send_string = str("<angular:{} ".format(angular) + "linear:{} ".format(linear) + "step:{}>".format(step_angle))

  # Send the string. Make sure you encode it before you send it to the Arduino.
  ser.write(send_string.encode('utf-8'))

  # Do nothing for 500 milliseconds (0.5 seconds)

  time.sleep(0.1)

  # Receive data from the Arduino
  receive_string = ser.readline().decode('utf-8').rstrip()

  # Print the data received from Arduino to the terminal
  print(receive_string)
  angular += 1
  linear += 1
