'''
Created on 30 Jul 2014

@author: matt
'''

from pi3d.shape.Plane import Plane
from pi3d.shape.MergeShape import MergeShape
import math


class Line2d(MergeShape):
    '''
    A 2d line with thickness
    '''

    def __init__(self, camera, matsh, points, thickness, colour=(255,255,255,255)):
        '''
        Constructor
        '''
        super(Line2d, self).__init__(camera)
        
        index = 0
        for i in xrange(0,len(points)-1):
            x1 = points[i][0]
            y1 = points[i][1]
            x2 = points[i+1][0]
            y2 = points[i+1][1]

            xdelta = (x2-x1)
            ydelta = (y2-y1)

            length = math.sqrt( (xdelta*xdelta) + (ydelta*ydelta) )
            xcenter=(x1+x2)*0.5
            ycenter=(y1+y2)*0.5
            
            if(xdelta != 0):
                angle = math.atan(ydelta / xdelta)
            else:
                angle = math.pi * 0.5
                
            if(ydelta < 0):
                angle += math.pi
                
            line = Plane(camera=camera,  w=length, h=thickness)
            line.set_draw_details(matsh, [], 0, 0)
#            line.set_material(colour)
#            line.rotateToZ(45)

            self.add(line, x=xcenter, y=ycenter, rz=math.degrees(angle))
            
        self.set_draw_details(matsh, [], 0, 0)
        self.set_material(colour)
#        self.rotateToZ(45)