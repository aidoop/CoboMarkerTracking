
import numpy as np
import cv2
import os
import sys
import datetime
import argparse

# add src root directory to python path
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))) )
from Config
from packages.CameraDevOpencv import OpencvCapture
from packages.CameraDevRealsense import RealsenseCapture
from packages.CameraVideoCapture import VideoCapture
from CalibCamera import CalibrationCamera
from CalibCameraKeyHandler import CalibCameraKeyHandler

# create a directory to save captured images 
def makeFrameImageDirectory():
    now = datetime.datetime.now()
    dirString = now.strftime("%Y%m%d%H%M%S")
    try:
        if not(os.path.isdir(dirString)):
            os.makedirs(os.path.join('../','Captured', dirString))
    except OSError as e:
        print("Can't make the directory: %s" % dirFrameImage)
        raise
    return os.path.join('../','Captured', dirString)

###############################################################################
# Hand-eye calibration process 
#   -                                                                
###############################################################################

if __name__ == '__main__':

    # parse program parameters to get necessary aruments
    argPar = argparse.ArgumentParser(description="Camera Calibration")
    argPar.add_argument('--camType', type= str, default='rs', choices=['rs', 'uvc'], metavar='CameraType', help = 'Camera Type(rs: Intel Realsense, uvc: UVC-Supported')
    argPar.add_argument('camIndex', type= int, metavar='CameraIndex', help = 'Camera Index(zero-based)')
    argPar.add_argument('frameWidth', type= int, metavar='FrameWidth', help = 'Camera Frame Width')
    argPar.add_argument('frameHeight', type= int, metavar='FrameHeight', help = 'Camera Frame Height')
    argPar.add_argument('fps', type= int, metavar='FPS', help = 'Camera Frame Per Seconds')
    argPar.add_argument('chessWidth', type= int, metavar='ChessBoardWidth', help = 'Chess Board Width')
    argPar.add_argument('chessHeight', type= int, metavar='ChessBoardHeight', help = 'Chess Board Height')
    args = argPar.parse_args()

    # create the camera device object
    if(args.camType == 'rs'):
        rsCamDev = RealsenseCapture(args.camIndex)
    elif(args.camType == 'uvc'):
        rsCamDev = OpencvCapture(args.camIndex)

    # create video capture object using realsense camera device object
    vcap = VideoCapture(rsCamDev, args.frameWidth, args.frameHeight, args.fps)

    # Start streaming
    vcap.start()

    # create a camera calibration object
    calibcam = CalibrationCamera(args.chessWidth, args.chessHeight)

    # TODO: check where an image directory is created..
    dirFrameImage = makeFrameImageDirectory()

    # create key handler for camera calibration1
    keyhandler = CalibCameraKeyHandler()

    print("press 'c' to capture an image")
    print("press 'g' to calcuate the result using the captured images")
    print("press 'q' to exit...")
    iteration = 0
    try: 
        while(True):
            # Wait for a coherent pair of frames: depth and color
            color_image = vcap.getFrame()

            # display the captured image
            cv2.imshow('Capture Images',color_image)
            pressedKey = (cv2.waitKey(1) & 0xFF)

            # TODO: arrange these opencv key events based on other key event handler class
            # handle key inputs
            if keyhandler.processKeyHandler(pressedKey, color_image, dirFrameImage, calibcam):
                break
    finally:
        # Stop streaming
        vcap.stop()

    cv2.destroyAllWindows()

