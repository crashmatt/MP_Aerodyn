from __future__ import absolute_import, division, print_function, unicode_literals

from pi3d.constants import *
from pi3d.Buffer import Buffer
from pi3d.Shape import Shape
import numpy as np
from numpy import dtype

class CPlanes(Shape):
  """ Draws a group of disconnected coloured planes. Uses normals as colour and no textures. Only flat material shaders and 2d cameras can be used"""
  def __init__(self, camera=None, light=None, name="",
               x=0.0, y=0.0, z=0.0,
               rx=0.0, ry=0.0, rz=0.0,
               sx=1.0, sy=1.0, sz=1.0,
               cx=0.0, cy=0.0, cz=0.0):
    """uses standard constructor for Shape extra Keyword arguments:

      *w*
        width
      *h*
        height
    """
    super(CPlanes, self).__init__(camera, light, name, x, y, z, rx, ry, rz,
                                sx, sy, sz, cx, cy, cz)

    if VERBOSE:
      print("Creating plane ...")

    self.ttype = GL_TRIANGLES
    self.verts = np.zeros((0,3), dtype=np.float)
    self.norms = np.zeros((0,3), dtype=np.float)
    self.texcoords = np.zeros((0,2), dtype=np.float)
    self.inds = np.zeros((0,3), dtype=np.int)
    self.planes = []

#    self.texcoords = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))


    self.buf = []

  def add_plane(self, pts, colour):
    norms = np.zeros((4,3), dtype=np.float)
    verts = np.zeros((4,3), dtype=np.float)
    inds = np.zeros((2,3), dtype=np.float)
    alphas = np.zeros((4,2), dtype=np.float)
    ind_count = len(self.verts)
    if len(colour) > 3:
        alpha = colour[3]
    else:
        alpha = 1.0
    
    for index in range(0,4):
        verts[index] = [ pts[index][0], pts[index][1], pts[index][2] ]
        norms[index] = [colour[0], colour[1], colour[2]]
        alphas[index] = [alpha, 0.0]

    inds = [ [ind_count, ind_count+1, ind_count+3], [ind_count+1, ind_count+2, ind_count+3] ]

    self.texcoords = np.append(self.texcoords, alphas, axis=0)
    self.verts = np.append(self.verts, verts, axis=0)
    self.norms = np.append(self.norms, norms, axis=0)
    self.inds = np.append(self.inds, inds, axis=0)
    
#===============================================================================
#     ww = 50
#     hh = 50
# 
#     self.verts = ((-ww, hh, 0.0), (ww, hh, 0.0), (ww, -hh, 0.0), (-ww, -hh, 0.0))
#===============================================================================
#    self.norms = ((0.0, 0.0, -1), (0.0, 0.0, -1),  (0.0, 0.0, -1), (0.0, 0.0, -1))
#    self.texcoords = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))

#    self.inds = ((0, 1, 3), (1, 2, 3))

  def init(self):
    self.buf.append(Buffer(self, self.verts, self.texcoords, self.inds, self.norms))
