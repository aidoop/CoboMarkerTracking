
import numpy as np
import cv2
import cv2.aruco as aruco
import os
import time
import datetime
import glob
import sys
import argparse

# add src root directory to python path
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))) )
import Config
from packages.CameraDevRealsense import RealsenseCapture
from packages.CameraDevOpencv import OpencvCapture
from packages.CameraVideoCapture import VideoCapture
import json
from packages.Aruco import ArucoDetect

import math

###############################################################################
# Hand-eye calibration process 
#   -                                                                
###############################################################################

if __name__ == '__main__':
    
    # camera index
    rsCamIndex = '4'
    #rsCamDev = RealsenseCapture(rsCamIndex)
    rsCamDev = OpencvCapture(int(rsCamIndex))
    vcap = VideoCapture(rsCamDev, Config.VideoFrameWidth, Config.VideoFrameHeight, Config.VideoFramePerSec, 'camera02')

    # Start streamingq
    vcap.start()

    # get instrinsics
    mtx, dist = vcap.getIntrinsicsMat(int(rsCamIndex), Config.UseRealSenseInternalMatrix)

    # create an aruco detect object
    arucoDetect = ArucoDetect(aruco.DICT_6X6_1000, 0.0375, mtx, dist)
    #arucoDetect = ArucoDetect(Config.ArucoDict, 0.075, mtx, dist)
    #arucoDetect = ArucoDetect(aruco.DICT_7X7_250, 0.05, mtx, dist)
    

    try:
        while(True):
            # Wait for a coherent pair of frames: depth and color
            color_image = vcap.getFrame()

            # operations on the frame
            gray = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)

            # lists of ids and the corners belonging to each id
            corners, ids = arucoDetect.detect(gray)
            if (corners is not None) and (ids is not None):

                # rvet and tvec-different from camera coefficients
                poseret, rvec, tvec = arucoDetect.estimatePoseBoard(corners, ids)

                if poseret >= 4:
                    # draw a cooordinate axis(x, y, z)
                    arucoDetect.drawAx(color_image, rvec, tvec, 16.5)

            # displaqy the captured image
            cv2.imshow('Prcision Test', color_image)

            # TODO: arrange these opencv key events based on other key event handler class
            # handle key inputs
            pressedKey = (cv2.waitKey(1) & 0xFF)
            if(pressedKey == ord('q')):
                break

    except Exception as ex:
        print("Error :", ex)

    finally:
        # Stop streaming
        vcap.stop()

    cv2.destroyAllWindows()
