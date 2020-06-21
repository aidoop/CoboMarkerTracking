from abc import *

from ROIManager import ROIManager

# 
class ROIRetangleManager(ROIManager):

    def __init__(self):
        self.RectangleROIList = []

    def appendROI(self, roi):
        self.RectangleROIList.append(roi)

    def getROIList(self):
        return self.RectangleROIList

    def isInsideROI(self, newRegion):
        isInside = False
        for idx in range(len(self.RectangleROIList)):
            isInside = self.contains(newRegion, self.RectangleROIList[idx])
            if(isInside == True):
                break
        return (isInside, idx)

    def clearROIAll(self):
        self.RectangleROIList.clear()
    
    def contains(self, newRegion, ROIRegion):
        topA = min(newRegion[0][0], newRegion[1][0], newRegion[2][0], newRegion[3][0])
        bottomA = max(newRegion[0][0], newRegion[1][0], newRegion[2][0], newRegion[3][0])
        leftA = min(newRegion[0][1], newRegion[1][1], newRegion[2][1], newRegion[3][1])
        rightA = max(newRegion[0][1], newRegion[1][1], newRegion[2][1], newRegion[3][1])

        topB = min(ROIRegion[0][0], ROIRegion[1][0])
        bottomB = max(ROIRegion[0][0], ROIRegion[1][0])
        leftB = min(ROIRegion[0][1], ROIRegion[1][1])
        rightB = max(ROIRegion[0][1], ROIRegion[1][1])

        # check if any point of A is outside B
        if( bottomA >= bottomB ):
            return False
        if( topA <= topB ):
            return False
        if( rightA >= rightB ):
            return False
        if( leftA <= leftB ):
            return False

        # none of the sides from A are outside B
        return True



        


