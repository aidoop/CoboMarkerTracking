import cv2
from time import sleep

from aidobjtrack.config.appconfig import AppConfig
from aidobjtrack.abc.keyhandlerdev import KeyHandler
from aidobjtrack.robot.robot_dev_indydcp import RobotIndy7Dev
from aidobjtrack.robot.robot_arm import RobotArm
from aidobjtrack.util.util import PrintMsg
from aidobjtrack.util.hm_util import *
from aidobjtrack.handeye.calibhandeye_handeye import *
from aidobjtrack.data_update.calibhandeye_update import CalibHandeyeUpdate
from aidobjtrack.handeye.calibhandeye_auto_move import HandEyeAutoMove


class CalibHandEyeKeyHandler(KeyHandler):

    def __init__(self):
        super().__init__()
        super().setKeyHandler('q', self.processQ)
        super().setKeyHandler('d', self.processD)
        super().setKeyHandler('f', self.processF)
        super().setKeyHandler('r', self.processR)
        super().setKeyHandler('c', self.processC)
        super().setKeyHandler('z', self.processZ)
        super().setKeyHandler('g', self.processG)

        # get the currenet marker position using predefined handeye matrix
        super().setKeyHandler('f', self.processF)

        # get the corrected matrix between BASE and CAMERA
        super().setKeyHandler('k', self.processK)

        # run the automated handeye calibration
        super().setKeyHandler('a', self.processA)

        self.interation = 0

    def processQ(self, *args):
        super().enableExitFlag()

    def processD(self, *args):
        robot_arm = args[8]
        # set direct-teaching mode on
        PrintMsg.printStdErr("direct teaching mode: On")
        robot_arm.set_teaching_mode(True)

    def processF(self, *args):
        robot_arm = args[8]
        # set direct-teaching mode off
        PrintMsg.printStdErr("direct teaching mode: Off")
        robot_arm.set_teaching_mode(False)

    def processR(self, *args):
        robot_arm = args[8]
        robot_arm.reset_robot()
        PrintMsg.printStdErr("resetting the robot")

    def processC(self, *args):
        findAruco = args[0]
        colorImage = args[1]
        tvec = args[3]
        rvec = args[4]
        ids = args[2]
        handeye = args[7]
        robot_arm = args[8]
        infoText = args[9]

        PrintMsg.printStdErr(
            "---------------------------------------------------------------")
        if ids is None:
            return

        if AppConfig.UseArucoBoard == False:
            for idx in range(0, ids.size):
                if(ids[idx] == AppConfig.CalibMarkerID):
                    # get the current robot position
                    currTaskPose = robot_arm.get_task_pos()

                    # capture additional matrices here
                    handeye.captureHandEyeInputs(
                        currTaskPose, rvec[idx], tvec[idx])

                    if handeye.cntInputData >= 3:
                        handeye.calculateHandEyeMatrix()

                    PrintMsg.printStdErr(
                        "Input Data Count: " + str(handeye.cntInputData))
                    strText = "Input Data Count: " + \
                        str(handeye.cntInputData) + \
                        "(" + str(handeye.distance) + ")"
                    infoText.setText(strText)
        else:
            if findAruco is True:
                # get the current robot position
                currTaskPose = robot_arm.get_task_pos()

                # capture additional matrices here
                handeye.captureHandEyeInputs(currTaskPose, rvec.T, tvec.T)

                if handeye.cntInputData >= 3:
                    handeye.calculateHandEyeMatrix()

                PrintMsg.printStdErr(
                    "Input Data Count: " + str(handeye.cntInputData))
                strText = "Input Data Count: " + \
                    str(handeye.cntInputData) + \
                    "(" + str(handeye.distance) + ")"
                infoText.setText(strText)

    def processZ(self, *args):
        handeye = args[7]
        handeye.resetHandEyeInputs()

    def processG(self, *args):
        handeye = args[7]
        infoText = args[9]

        if handeye.cntInputData < 3:
            return

        PrintMsg.printStdErr(
            "---------------------------------------------------------------")
        hmTransform = handeye.getHandEyeResultMatrixUsingOpenCV()
        PrintMsg.printStdErr("Transform Matrix = ")
        PrintMsg.printStdErr(hmTransform)
        HandEyeCalibration.saveTransformMatrix(hmTransform)

        updateUI = CalibHandeyeUpdate()
        # TODO: [0] is available??
        updateUI.updateData(hmTransform.reshape(1, 16)[0])

        infoText.setText('Succeeded to extract a handeye matrix.')

    def processN(self, *args):
        tvec = args[3]
        rvec = args[4]
        ids = args[2]
        handeye = args[7]
        robot_arm = args[8]
        infoText = args[9]

        PrintMsg.printStdErr(
            "---------------------------------------------------------------")
        for idx in range(0, ids.size):
            if ids[idx] == AppConfig.TestMarkerID:
                # change a rotation vector to a rotation matrix
                rotMatrix = np.zeros(shape=(3, 3))
                cv2.Rodrigues(rvec[idx], rotMatrix)

                # make a homogeneous matrix using a rotation matrix and a translation matrix a
                hmCal2Cam = HMUtil.makeHM(rotMatrix, tvec[idx])

                # get a transformation matrix which was created by calibration process
                hmmtx = HandEyeCalibration.loadTransformMatrix()

                # calcaluate the specific position based on hmInput
                hmWanted = HMUtil.makeHM(np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [
                                         0.0, 0.0, 1.0]]), np.array([0.0, 0.0, AppConfig.HandEyeTargetZ]).T)
                # hmWanted = HMUtil.makeHM(np.array([[1.0, 0.0, 0.0],[0.0, 1.0, 0.0],[0.0, 0.0, 1.0]]), np.array([0.08, 0.0, 0.0]).T)
                # hmWanted = HMUtil.makeHM(np.array([[1.0, 0.0, 0.0],[0.0, 1.0, 0.0],[0.0, 0.0, 1.0]]), np.array([0.0, 0.0, 0.0]).T)
                # hmWanted = HMUtil.makeHM(np.array([[1.0, 0.0, 0.0],[0.0, 1.0, 0.0],[0.0, 0.0, 1.0]]), np.array([0.0, 0.0, 0.0]).T)

                hmInput = np.dot(hmCal2Cam, hmWanted)

                # get the last homogeneous matrix
                hmResult = np.dot(hmmtx, hmInput)

                # get a final xyzuvw for the last homogenous matrix
                xyzuvw = HMUtil.convertHMtoXYZABCDeg(hmResult)
                PrintMsg.printStdErr("Final XYZUVW: ")
                PrintMsg.printStdErr(xyzuvw)

                ############################################################################################
                # test move to the destination
                [x, y, z, u, v, w] = xyzuvw

                # indy7 base position to gripper position
                xyzuvw = [x, y, z, u*(-1), v+180.0, w]  # test w+180
                PrintMsg.printStdErr("Modifed TCP XYZUVW: ")
                PrintMsg.printStdErr(xyzuvw)
                # robot_arm.move_task_to(xyzuvw)

                curjpos = robot_arm.get_joint_pos()
                nextMoveAvail = robot_arm.check_next_move(xyzuvw, curjpos)
                print('nextMoveAvail: ', nextMoveAvail)
                print('currentTaskPos: ', robot_arm.get_task_pos())
                print('nextTaskMove: ', xyzuvw)

                if(nextMoveAvail != [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]):
                    robot_arm.move_task_to(xyzuvw)
                else:
                    xyzuvw = [x, y, z, u*(-1), v+180.0, w+180]
                    robot_arm.move_task_to(xyzuvw)

                # # get a HM from TCP to Base
                # hmRecal = HMUtil.convertXYZABCtoHMDeg(xyzuvw)
                # #
                # hmWanted2 = HMUtil.makeHM(np.array([[1.0, 0.0, 0.0],[0.0, 1.0, 0.0],[0.0, 0.0, 1.0]]), np.array([0.0, 0.0, -0.3]).T)
                # hmResult2 = np.dot(hmRecal, hmWanted2)
                # xyzuvw2 = HMUtil.convertHMtoXYZABCDeg(hmResult2)
                # PrintMsg.printStdErr("Recalculated XYZUVW: ")
                # PrintMsg.printStdErr(xyzuvw2)

    def processF(self, *args):
        tvec = args[3]
        rvec = args[4]
        ids = args[2]
        handeye = args[7]
        robot_arm = args[8]

        for idx in range(0, ids.size):
            if ids[idx] == AppConfig.CalibMarkerID:
                print('---------------------------------------')

                # get the current robot position
                robot_curr_pos = robot_arm.get_task_pos()
                print('current robot position: ', robot_curr_pos)

                # get the current camera-based matrix
                rotMatrix = np.zeros(shape=(3, 3))
                cv2.Rodrigues(rvec[idx], rotMatrix)
                hmCal2Cam = HMUtil.makeHM(rotMatrix, tvec[idx])

                # get the predefined handeye matrix
                hmHandEye = handeye.getHandEyeMatUsingMarker(
                    robot_curr_pos, rvec[idx], tvec[idx])

                # get the final matrix
                hmFinal = np.dot(hmHandEye, hmCal2Cam)
                print('hmFinal: ', hmFinal)
                final_xyzuvw = HMUtil.convertHMtoXYZABCDeg(hmFinal)
                print('final_xyzuvw: ', final_xyzuvw)

    def processK(self, *args):
        tvec = args[3]
        rvec = args[4]
        ids = args[2]
        handeye = args[7]
        robot_arm = args[8]

        for idx in range(0, ids.size):
            if ids[idx] == AppConfig.CalibMarkerID:
                print('---------------------------------------')

                # get the current robot position
                robot_curr_pos = robot_arm.get_task_pos()
                print('robot position: ', robot_curr_pos)

                # get the predefined handeye matrix
                hmHandEye = handeye.getHandEyeMatUsingMarker(
                    robot_curr_pos, rvec[idx], tvec[idx])
                xyzuvwHandEye = HMUtil.convertHMtoXYZABCDeg(hmHandEye)
                print('handeye :', xyzuvwHandEye)
                print('hmHandEye :', hmHandEye)

    # automated handeye calibration

    def processA(self, *args):
        tvec = args[3]
        rvec = args[4]
        ids = args[2]
        handeye = args[7]
        robot_arm = args[8]
        handeye_automove = args[10]

        handeye_automove.start()
