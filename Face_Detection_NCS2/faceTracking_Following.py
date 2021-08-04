running_on_rpi = False
# import os

# os_info = os.uname()
# if os_info[4][:3] == 'arm':
#     running_on_rpi = True

from imutils.video import VideoStream
from imutils.video import FPS
import argparse
import time
import cv2
import serial


#-------------------------- Load the model-------------------------------------------------#
net = cv2.dnn.readNet('models/face-detection-adas-0001.xml', 'models/face-detection-adas-0001.bin')

#-------------------------- Specify target device -----------------------------------------#
net.setPreferableTarget(cv2.dnn.DNN_TARGET_MYRIAD)

#-------------------------- Setup Serial Communication with Arduino --------------------------#
ser = serial.Serial('COM6', 9600, timeout=.0000001)
# Get rid of garbage/incomplete data
ser.flush()
#-------------------------- Setup Serial Communication with Arduino --------------------------#

resX = 672
resY = 384

cx = resX / 2
cy = resY / 2

xdeg = 0
angular = 0
linear = 0
#step degree

def predict(frame, net):
    # Prepare input blob and perform an inference
    blob = cv2.dnn.blobFromImage(frame, size=(672, 384), ddepth=cv2.CV_8U)
    net.setInput(blob)
    out = net.forward()
    predictions = []
    # Draw detected faces on the frame
    for detection in out.reshape(-1, 7):
        conf = float(detection[2])
        xmin = int(detection[3] * frame.shape[1])
        ymin = int(detection[4] * frame.shape[0])
        xmax = int(detection[5] * frame.shape[1])
        ymax = int(detection[6] * frame.shape[0])

        if conf > args["confidence"]:
            pred_boxpts = ((xmin, ymin), (xmax, ymax))
            # create prediction tuple and append the prediction to the
            # predictions list
            tx = (xmin + xmax)/2
            ty = (ymin + ymax)/2
            position = (tx, ty)
            surface = (ymax - ymin)*(xmax - xmin)
            prediction = (conf, pred_boxpts, position, surface)
            predictions.append(prediction)

            
    # return the list of predictions to the calling function
    return predictions


# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-c", "--confidence", default=.5,
                help="confidence threshold")
ap.add_argument("-d", "--display", type=int, default=1,
                help="switch to display image on screen")
ap.add_argument("-i", "--input", type=str,
                help="path to optional input video file")
args = vars(ap.parse_args())


# if a video path was not supplied, grab a reference to the webcam
if not args.get("input", False):
    print("[INFO] starting video stream...")
    # cap = cv2.VideoCapture(0)
    vs = VideoStream(src=0).start()
    time.sleep(2.0)

# otherwise, grab a reference to the video file
else:
    print("[INFO] opening video file...")
    vs = cv2.VideoCapture(args["input"])

time.sleep(1)
fps = FPS().start()

# loop over frames from the video file stream
while True:
    try:
        # grab the frame from the threaded video stream
        # make a copy of the frame and resize it for display/video purposes
        frame = vs.read()
        frame = frame[1] if args.get("input", False) else frame
        image_for_result = frame.copy()

        # use the NCS to acquire predictions
        predictions = predict(frame, net)

        # loop over our predictions
        for (i, pred) in enumerate(predictions):
            # extract prediction data for readability
            (pred_conf, pred_boxpts, pred_position, pred_surface) = pred

            # filter out weak detections by ensuring the `confidence`
            # is greater than the minimum confidence
            if pred_conf > args["confidence"]:
                # print prediction to terminal
                print("[INFO] Prediction #{}: confidence={}, "
                      "boxpoints={}".format(i, pred_conf,
                                            pred_boxpts))

                # check if we should show the prediction data
                # on the frame
                if args["display"] > 0:
                    # build a label
                    label = "person: {:.2f}%".format(pred_conf * 100)

                    # extract information from the prediction boxpoints
                    (ptA, ptB) = (pred_boxpts[0], pred_boxpts[1])
                    (startX, startY) = (ptA[0], ptA[1])
                    y = startY - 15 if startY - 15 > 15 else startY + 15

                    # display the rectangle and label text
                    cv2.rectangle(image_for_result, ptA, ptB,
                                  (255, 0, 0), 2)
                    cv2.putText(image_for_result, label, (startX, y),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
                    tx = pred_position[0]
                    ty = pred_position[1]
                    if   ( cx - tx > 100 ): #left
                        #xdeg += 1
                        angular = -2 
                        linear = 0    
                    if ( cx - tx < -100 ): #right 
                        #xdeg -= 1
                        angular = 2
                        linear = 0
                    if ( -100 < cx - tx < 100):
                        linear = 0.2
                        angular = 0
                    
                    send_string = str("<angular:{}>".format(angular))
                    ser.write(send_string.encode('utf-8'))
                    #if   ( cy - ty > 15 and ydeg >= 90 ):
                       # ydeg -= 2
                       # print("\n")
                        #print(ydeg)
                    #elif ( cy - ty < -15 and ydeg <= 180 ): 
                      #  ydeg += 2
                       # print("\n")
                       # print(ydeg)
        # check if we should display the frame on the screen
        # with prediction data (you can achieve faster FPS if you
        # do not output to the screen)
        if args["display"] > 0:
            # display the frame to the screen
            cv2.imshow("Output", image_for_result)
            key = cv2.waitKey(1) & 0xFF

            # if the `q` key was pressed, break from the loop
            if (pred_surface > 60000):
                xdeg -= 0
                angular = 0
                linear = 0
                #send_string = str("<angular:{} ".format(angular) + "linear:{} ".format(linear) + "step:{}>".format(xdeg))
                #ser.write(send_string.encode('utf-8'))
                break
            if key == ord("q"):
                xdeg -= 0
                angular = 0
                linear = 0
                #send_string = str("<angular:{} ".format(angular) + "linear:{} ".format(linear) + "step:{}>".format(xdeg))
                #ser.write(send_string.encode('utf-8'))
                break

        # update the FPS counter
        fps.update()

    # if "ctrl+c" is pressed in the terminal, break from the loop
    except KeyboardInterrupt:
        break

    # if there's a problem reading a frame, break gracefully
    except AttributeError:
        break

# stop the FPS counter timer
fps.stop()

# destroy all windows if we are displaying them
if args["display"] > 0:
    cv2.destroyAllWindows()

# if we are not using a video file, stop the camera video stream
if not args.get("input", False):
    vs.stop()

# otherwise, release the video file pointer
else:
    vs.release()

# display FPS information
print("[INFO] elapsed time: {:.2f}".format(fps.elapsed()))
print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))