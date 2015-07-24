'''
Created on 16 Jul 2015

@author: matt
'''

import pi3d
from pi3d.util.OffScreenTexture import OffScreenTexture
from pi3d.shape.FlipSprite import FlipSprite

class MapTile(object):
    '''
    classdocs
    '''


    def __init__(self, map_camera, tilePixels, tile_x, tile_y):
        '''
        tilePixels = size of tile in pixels
        '''
        from pi3d.Display import Display
               
        self.tilePixels = tilePixels
        
        tilename = "maptile [%d],[%d]", tile_x, tile_y
        xpos = float(tile_x*tilePixels)
        ypos = float(tile_y*tilePixels)

        self.texture = OffScreenTexture(name="map_tile",  w=self.tilePixels, h=self.tilePixels)
        self.sprite = FlipSprite(camera=map_camera, w=self.tilePixels, h=self.tilePixels, z=6.0, x=xpos, y=ypos
                                 , flip=True)
        