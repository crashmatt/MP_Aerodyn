'''
Created on 30 Jul 2014

@author: matt
'''

#from pi3d.shape.Plane import Plane
from pi3d.shape.Lines import Lines
import math


class Lines2d(Lines):
    '''
    A 2d line based on 3d lines
    '''

    def __init__(self,  camera=None, light=None, points=[], material=(1.0,1.0,1.0),
               line_width=1, closed=False, name="", x=0.0, y=0.0, z=0.0,
               sx=1.0, sy=1.0, sz=1.0, rx=0.0, ry=0.0, rz=0.0,
               cx=0.0, cy=0.0, cz=0.0):
        '''uses standard constructor for Shape extra Keyword arguments:
    
          *points*
            array of points [(x0,y0),(x1,y1)..]
          *material*
            tuple (r,g,b)
          *line_width*
            set to 1 if absent or set to a value less than 1
          *closed*
            joins up last leg i.e. for polygons
        '''
        
        vertices = []
        for point in points:
            vertice = (point[0], point[1], 0)
            vertices.append(vertice)
    
        super(Lines2d, self).__init__(camera, light, vertices, material,
               line_width, closed, name, x, y, z,
               sx, sy, sz, rx, ry, rz,
               cx, cy, cz)
        
        
        