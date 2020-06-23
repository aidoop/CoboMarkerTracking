import cv2
import cv2.aruco as aruco

import sys, os
import argparse
import time

# add src root directory to python path
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))) )
import Config
from packages.CameraDevRealsense import RealsenseCapture
from packages.CameraVideoCapture import VideoCapture
from ObjectArucoMarkerTracker import ArucoMarkerObject, ArucoMarkerTracker
from ObjectTrackingKeyHandler import ObjectTrackingKeyHandler
from ROIRetangleManager import ROIRetangleManager


###############################################################################
# Hand-eye calibration process 
#   -                                                                
###############################################################################

if __name__ == '__main__':

    # parse program parameters to get necessary aruments
    argPar = argparse.ArgumentParser(description="HandEye Calibration")
    argPar.add_argument('--camType', type= str, default='rs', choices=['rs', 'uvc'], metavar='CameraType', help = 'Camera Type(rs: Intel Realsense, uvc: UVC-Supported')
    argPar.add_argument('camIndex', type= int, metavar='CameraIndex', help = 'Camera Index(zero-based)')
    argPar.add_argument('frameWidth', type= int, metavar='FrameWidth', help = 'Camera Frame Width')
    argPar.add_argument('frameHeight', type= int, metavar='FrameHeight', help = 'Camera Frame Height')
    argPar.add_argument('fps', type= int, metavar='FPS', help = 'Camera Frame Per Seconds')
    argPar.add_argument('-l', '--list', action='append', metavar='ArucoMarkIDs', help = 'Aruco Mark Infos (ID, PivotOffset(XYZUVW)) ex) -l 14, 0.0, 0.0, 0.1, 0.0, 0.0, 0.0')
    argPar.add_argument('duration', type= float, metavar='ProcessDuration', help = 'Process Duration(sec)')
    args = argPar.parse_args()
    arucoParamList = args.list


    # TODO: get object, camera workspace from gql server




    # create the camera device object
    if(args.camType == 'rs'):
        rsCamDev = RealsenseCapture(args.camIndex)
    elif(args.camType == 'uvc'):
        rsCamDev = OpencvCapture(args.camIndex)


    # create video capture object using realsense camera device object
    vcap = VideoCapture(rsCamDev, args.frameWidth, args.frameHeight, args.fps)


    # rsCamDev2 = RealsenseCapture(1)
    # vcap2 = VideoCapture(rsCamDev2, args.frameWidth, args.frameHeight, args.fps)


    # Start streaming
    vcap.start()
    # vcap2.start()

    # get instrinsics
    mtx, dist = vcap.getIntrinsicsMat(Config.UseRealSenseInternalMatrix)

    # TODO: need to make 
    # create objs and an object tracker 
    objTracker = ArucoMarkerTracker()
    objTracker.initialize(aruco.DICT_5X5_250, 0.05, mtx, dist)
    for argParam in arucoParamList:
        parsedData = argParam.split(',')
        obj = ArucoMarkerObject(int(parsedData[0]), [float(parsedData[1]), float(parsedData[2]), float(parsedData[3]), float(parsedData[4]), float(parsedData[5]), float(parsedData[6])])
        objTracker.setTrackingObject(obj)    

    # TODO: this kinds of file process should be moved together to a specific module.
    # load ROI Region from a json file
    ROIMgr = ROIRetangleManager()
    ROIRegionFile = cv2.FileStorage("ROIRegions.json", cv2.FILE_STORAGE_READ)
    roiCntNode = ROIRegionFile.getNode("ROICnt")
    roiCnt = int(roiCntNode.real())
    for idx in range(roiCnt):
        ROIRegionNode = ROIRegionFile.getNode("ROI" + str(idx))
        ROIMgr.appendROI(ROIRegionNode.mat())
    ROIRegionFile.release()

    # creat key handler
    keyhandler = ObjectTrackingKeyHandler()

    #print("press 'c' to capture an image or press 'q' to exit...")
    try:
        while(True):
            # wait for a coherent pair of frames: depth and color
            color_image = vcap.getFrame()
            #color_image2 = vcap2.getFrame()

            # detect markers here..
            resultObjs = objTracker.findObjects(color_image, mtx, dist)

            # draw ROI Region..
            for ROIRegion in ROIMgr.getROIList():
                cv2.rectangle(color_image, tuple(ROIRegion[0]), tuple(ROIRegion[1]), (255,0,0), 3)

            # iterate the final object list
            for resultObj in resultObjs:
                print(resultObj)
                print(ROIMgr.isInsideROI(resultObj.corners))
                # TODO: if any marker is inside ROI, send marker data to Node.JS using the result list here...

            # display the captured image
            cv2.imshow('Object Tracking Engine',color_image)
            #cv2.imshow('Object Tracking Engine2',color_image2)

            # sleep for the specific duration.
            time.sleep(args.duration)

            # handle key inputs
            pressedKey = (cv2.waitKey(1) & 0xFF)
            if keyhandler.processKeyHandler(pressedKey):
                break
    finally:
        # Stop streaming
        vcap.stop()

    cv2.destroyAllWindows()

