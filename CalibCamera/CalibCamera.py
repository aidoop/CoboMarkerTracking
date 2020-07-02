
import numpy as np
import cv2
import os
import datetime
import glob
import sys

class CalibrationCamera:
    
    def __init__(self, chessboardX, chessboardY):
        # prepare arrays to store object points and image points from all the images.
        # 3d point in real world space
        self.objpoints = [] 
        # 2d points in image plane.
        self.imgpoints = [] 
        # width and height of chessboard 
        self.chessboardX = chessboardX  
        self.chessboardY = chessboardY

        # reprojection error criterion
        self.REPROERR_CRITERION = 1.0

    def calcuateCameraMatrix(self, images):
        # opencv algorithm termination criteria
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

        # prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(9,6,0)
        objp = np.zeros((self.chessboardY*self.chessboardX,3), np.float32)
        objp[:,:2] = np.mgrid[0:self.chessboardX,0:self.chessboardY].T.reshape(-1,2)

        for fname in images:
            print(fname, file=sys.stderr)
            img = cv2.imread(fname)
            gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

            # Find the chess board corners
            ret, corners = cv2.findChessboardCorners(gray, (self.chessboardX,self.chessboardY),None)

            # If found, add object points, image points (after refining them)
            if ret == True:
                # append the set of object points like (0,0,0), (1,0,0), (2,0,0), ...
                self.objpoints.append(objp)

                # refine corners coordinates
                corners2 = cv2.cornerSubPix(gray,corners,(11,11),(-1,-1),criteria)
                self.imgpoints.append(corners2)

        # start camera calibartion
        if (len(self.objpoints) > 0) and (len(self.imgpoints) > 0):
            reperr, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(self.objpoints, self.imgpoints, gray.shape[::-1], None, None)
            print("Reprojection Error: " + str(reperr), file=sys.stderr)

            # TODO: should check this reprojection eror is available...
            calibResult = True if reperr <= self.REPROERR_CRITERION else False
        else:
            calibResult = False
            mtx = None
            dist = None

        # return reprojection error
        return (calibResult, mtx, dist)

    def saveResults(self, fname, mtx, dist):
        #name, ext = os.path.splitext(fname)
        calibFile = cv2.FileStorage(fname, cv2.FILE_STORAGE_WRITE)
        calibFile.write("cameraMatrix", mtx)
        calibFile.write("distCoeff", dist)
        calibFile.release()

    def clearObjImgPoints(self):
        self.objpoints.clear()
        self.imgpoints.clear()
