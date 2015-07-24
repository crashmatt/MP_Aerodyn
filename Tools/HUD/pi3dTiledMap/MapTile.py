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


    def __init__(self, map_camera, shader, tilePixels, tile_x, tile_y):
        '''
        tilePixels = size of tile in pixels
        '''
        from pi3d.Display import Display
               
        self.tilePixels = tilePixels
        
        tilename = "maptile [%d],[%d]", tile_x, tile_y
        xpos = float(tile_x*tilePixels)
        ypos = float(tile_y*tilePixels)
        
        # camera for viewing the track. Owned by the track since it can move
        self.camera2d = pi3d.Camera(is_3d = False)
        
        self.map_camera = map_camera
        
        self.flatsh = shader    #pi3d.Shader("uv_flat")
        self.matsh = pi3d.Shader("mat_flat")
        
        self.screen_width = Display.INSTANCE.width
        self.screen_height = Display.INSTANCE.height
        
        self.texture = OffScreenTexture("track",  w=self.screen_width, h=self.screen_height)
        self.sprite = FlipSprite(camera=map_camera, w=self.screen_width, h=self.screen_height, z=5.0, flip=True)
        
#        self.texture = OffScreenTexture(name="map_tile",  w=self.tilePixels, h=self.tilePixels)
#        self.sprite = FlipSprite(camera=map_camera, w=self.tilePixels, h=self.tilePixels, z=6.0#, x=xpos, y=ypos
#                                 , flip=True)
        
        
    def draw(self):
#        self.sprite.set_alpha(alpha)
        self.camera2d.reset(is_3d=False)
        self.sprite.draw(self.flatsh, [self.texture], self.camera2d)
        
        