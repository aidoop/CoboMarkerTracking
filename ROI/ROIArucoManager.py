import os
import numpy as np
from typing import NamedTuple

import Config
import cv2
import cv2.aruco as aruco

# TODO: should be derived in abstract class??
class ROIAruco2DManager:
    
    def __init__(self):
        # arouco marker id list
        self.arucoRangeList = []

        # ROI Region List
        self.ROIRegions = []

    def setMarkIdPair(self, arucoRangeData):
        self.arucoRangeList.append(arucoRangeData)
        
    def clearMakrIdPair(self):
        self.arucoRangeList.clear()

    def setROIRegion(self, pixelCoord1, pixelCoord2):
        self.ROIRegions.append((pixelCoord1, pixelCoord2))
    
    def getROIRegition(self):
        return self.ROIRegions

    def clearROIRegion(self):
        self.ROIRegions.clear()

    def printRangeData(self):
        for rdata in self.arucoRangeList:
            print('Start: ' + str(rdata[0]) + ', End: ' + str(rdata[1]))

    def findROI(self, color_image, mtx, dist):
        # clear previous list
        self.clearROIRegion()

        # operations on the frame
        gray = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)

        # set dictionary size depending on the aruco marker selected
        aruco_dict = aruco.Dictionary_get(aruco.DICT_5X5_250)

        # detector parameters can be set here (List of detection parameters[3])
        parameters = aruco.DetectorParameters_create()
        parameters.adaptiveThreshConstant = 10

        # lists of ids and the corners belonging to each id
        corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

        if np.all(ids != None):
            # estimate pose of each marker and return the values
            # rvet and tvec-different from camera coefficients
            rvec, tvec ,_ = aruco.estimatePoseSingleMarkers(corners, Config.ArucoSize, mtx, dist)            

            centerPoint = dict()
            for arucoIDRange in self.arucoRangeList:
                if (arucoIDRange[0] in ids) and (arucoIDRange[1] in ids):
                    # get a retangle coordinates between two aruco marks
                    for arucoMark in arucoIDRange:
                        idx = list(ids).index(arucoMark)
                        inputObjPts = np.float32([[0.0,0.0,0.0]]).reshape(-1,3)
                        imgpts, jac = cv2.projectPoints(inputObjPts, rvec[idx], tvec[idx], mtx, dist)
                        centerPoint[arucoMark] = tuple(imgpts[0][0])

                    # set the current region to a list
                    self.setROIRegion(centerPoint[arucoIDRange[0]], centerPoint[arucoIDRange[1]])

        return self.getROIRegition()


    

       



###############################################################################
# sample codes
###############################################################################

if __name__ == '__main__':
    managerROI = ROIAruco2DManager()

    managerROI.setMarkIdPair((9,10))
    managerROI.setMarkIdPair((11,12))
    managerROI.printRangeData()
    