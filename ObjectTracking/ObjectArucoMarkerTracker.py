import cv2
import cv2.aruco as aruco

import numpy as np
import sys, os

# add src root directory to python path
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))) )
import Config
from ObjectTracker import ObjectTracker
from CalibHandEye.HandEye import HandEyeCalibration
from CalibHandEye.HandEyeUtilSet import HMUtil
from packages.Aruco import ArucoDetect

# TODO: should be derived in a abstraction class like TrackingObject later.......
class ArucoMarkerObject:
    def __init__(self, markerID, pivotOffset):
        self.markerID = markerID
        self.pivotOffset = pivotOffset
        self.corners = None
        self.targetPos = None

# 
class ArucoMarkerTracker(ObjectTracker):
    def __init__(self):
        self.markerObjectList = []
        self.markerObjIDList = []

    # initialize parameters for any camera operation
    def initialize(self, *args):
        self.markerSelectDict = args[0]
        self.markerSize = args[1]
        self.camMtx = args[2]
        self.dist = args[3]
        self.markerObjectList.clear()
        self.markerObjIDList.clear()
        self.handEyeMat = args[4] #HandEyeCalibration.loadTransformMatrix()
        self.arucoDetect = ArucoDetect(self.markerSelectDict, self.markerSize, self.camMtx, self.dist)

    ## set detectable features like marker id of aruco marker
    def setTrackingObject(self, object):
        assert(isinstance(object, ArucoMarkerObject))

        found = False
        for mo in self.markerObjectList:
            if object.markerID == mo.markerID:
                found = True
           
        if found is False:
            self.markerObjIDList.append(object.markerID)
            self.markerObjectList.append(object)

    def getTrackingObjectList(self):
        return self.markerObjectList

    def getTrackingObjIDList(self):
        return self.markerObjIDList

    ## set detectable features and return the 2D or 3D positons in case that objects are detected..
    def findObjects(self, *args):
        color_image = args[0]
        vtc = args[1]
        mtx = vtc.mtx
        dist = vtc.dist
        gripperOffset = args[2]

        # prepare list to give over the result objects
        resultList = list()

        gray = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)

        # # lists of ids and the corners belonging to each id
        corners, ids = self.arucoDetect.detect(gray)

        # set detected objects to the result list..
        if np.all(ids != None):
            # estimate pose of each marker and return the values
            rvec, tvec = self.arucoDetect.estimatePose(corners)

            for markerObject in self.markerObjectList:
                for idx in range(len(ids)):
                    if ids[idx] == markerObject.markerID:
                        # set additional properties to this found object..
                        #print(vtc.name, ") Found Target ID: " + str(markerObject.markerID))
                        markerObject.corners = corners[idx].reshape(4,2)    # reshape: (1,4,2) --> (4,2)

                        # change a rotation vector to a rotation matrix
                        rotMatrix = np.zeros(shape=(3,3))
                        cv2.Rodrigues(rvec[idx], rotMatrix)

                        # make a homogeneous matrix using a rotation matrix and a translation matrix
                        hmCal2Cam = HMUtil.makeHM(rotMatrix, tvec[idx])
                        xyzuvw_midterm = HMUtil.convertHMtoXYZABCDeg(hmCal2Cam)
                        #print("Esitmated Mark Pose: ", xyzuvw_midterm)

                        # calcaluate the modified position based on pivot offset
                        # if markerObject.pivotOffset is None:
                        #     hmWanted = HMUtil.convertXYZABCtoHMDeg([0.0, 0.0, 0.00, 0.0, 0.0, 0.0])     # fix z + 0.01 regardless of some input offsets like tool offset, poi offset,...
                        #     hmInput = np.dot(hmCal2Cam, hmWanted)
                        # else:
                        #     hmWanted = HMUtil.convertXYZABCtoHMDeg(markerObject.pivotOffset)                            
                        #     hmInput = np.dot(hmCal2Cam, hmWanted)
                        
                        # udpate a pivot offset
                        offsetPoint = markerObject.pivotOffset
                        
                        hmWanted = HMUtil.convertXYZABCtoHMDeg(offsetPoint)     # fix z + 0.01 regardless of some input offsets like tool offset, poi offset,...
                        hmInput = np.dot(hmCal2Cam, hmWanted)

                        ###########################################################################################
                        # TODO: should find out how to apply tool offset and poi offset here...

                        # get a final position
                        hmResult = np.dot(self.handEyeMat, hmInput)
                        xyzuvw = HMUtil.convertHMtoXYZABCDeg(hmResult)

                        # TODO:.............................................
                        # TODO: should change this routine....

                        # this conversion is gone to Operato..
                        # [x,y,z,u,v,w] = xyzuvw
                        # xyzuvw = [x,y,z,u*(-1),v+180.0,w]   # indy7 base position to gripper position

                        # set final target position..
                        markerObject.targetPos = xyzuvw                        

                        #print("Final XYZUVW: ", xyzuvw)
                  
                        # append this object to the list to be returned
                        resultList.append(markerObject)

                        # draw a cooordinate axis(x, y, z)
                        aruco.drawAxis(color_image, mtx, dist, rvec[idx], tvec[idx], 0.02)

            # draw a square around the markers
            aruco.drawDetectedMarkers(color_image, corners)

        return resultList

        


        




    