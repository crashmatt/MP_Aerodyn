'''
Created on 22 Aug 2015

@author: matt
'''

import pi3d

class TiledSprite(pi3d.Shape):
  def __init__(self, camera=None, shader= None, name="", light=None, tiles=[[0.0, 0.0, 1.0, 1.0, False]],
               x=0.0, y=0.0, z=20.0,):
    """
      *tiles*
        list of tiles [texture, x, y, w, h, flip]
    """
    super(TiledSprite, self).__init__(camera, light, name, x, y, z, 0.0, 0.0, 0.0,
                                 1.0, 1.0, 1.0, 0.0, 0.0, 0.0)
    self.buf = []
    for t in tiles:
      texture, x, y, w, h, flip = t[0:6]
      ww = w / 2.0
      hh = h / 2.0 if not flip else -h / 2.0
      verts = ((x-ww, y+hh, 0.0), (x+ww, y+hh, 0.0), (x+ww, y-hh, 0.0), (x-ww, y-hh, 0.0))
      norms = ((0, 0, -1), (0, 0, -1),  (0, 0, -1), (0, 0, -1))
      texcoords = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0 , 1.0))

      inds = ((3, 0, 1), (1, 2, 3)) if not flip else ((0, 3, 2), (2, 1, 0))

      b = pi3d.Buffer(self, verts, texcoords, inds, norms)
      b.shader = shader
      b.textures = [texture]
      self.buf.append(b)


