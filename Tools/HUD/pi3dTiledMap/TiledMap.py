'''
Created on 16 Jul 2015

@author: matt
'''

import pi3d
from pi3d.util.OffScreenTexture import OffScreenTexture
from pi3d.shape.FlipSprite import FlipSprite
from MapTile import MapTile
from _dbus_bindings import String
from math import sin, cos, log , pi, ceil


DEFAULT_ORIGIN = [0.0, 0.0]

class TiledMap(object):
    '''
    A tiled map system running under pi3d.  Organises and draws small parts of a map (tiles) from a larger collection. 
    '''


    def __init__(self, tileSize, w, h, z, tileResolution=1, alpha = 1.0):
        '''
        tileSize = size of tile in meters
        tileResolution = pixels per meter (not supported yet)
        w = Pixel height to show
        h = Pixel width to show
        z = Map stack depth
        alpha = transparency
        '''        
        from pi3d.Display import Display
        
        tileSize = 256
                
        self.tileSize = tileSize
        self.tileResolution = tileResolution
        self.tile_scale = 1 / (self.tileSize * self.tileResolution)

        self.w = w
        self.h = h
        self.z = z
        self.alpha = alpha

        self.zoom = 0
        
        self.tiles = dict()
        self.map_objects = list()
   
        # Map focus point    
        self.map_focus = DEFAULT_ORIGIN  # map focus [lon, lat]
        
        self.origin = DEFAULT_ORIGIN

        self.home_colour = (0,0,1.0,0.5)
        
        # camera for viewing the map. Owned by the track since it can move
        self.map_camera = pi3d.Camera(is_3d = False)

        # 2d camera for drawing on the map tiles
        self.tile_camera = pi3d.Camera(is_3d=False)    #pi3d.Camera(is_3d=False)

        # shader for drawing the map        
        self.flatsh = pi3d.Shader("uv_flat")
        
        #shader for drawing simple colour shapes on the map
        self.matsh = pi3d.Shader("mat_flat")
        
        self.screen_width = Display.INSTANCE.width
        self.screen_height = Display.INSTANCE.height
        
        self.cam_xoffset = (self.screen_width-tileSize) * 0.5
        self.cam_yoffset = (self.screen_height-tileSize) * 0.5
  
        self.tile = MapTile(map_camera=self.map_camera, map_shader = self.flatsh, tilePixels=self.tileSize, tile_x=0, tile_y=0)
  #      self.map_texture = OffScreenTexture("track",  w=tileSize, h=tileSize)
  #      self.sprite = FlipSprite(camera=self.map_camera, w=tileSize, h=tileSize, z=5, flip=True)
        self.tiles = dict()
        self.tiles["0,0"] = self.tile
                
        self.inits_done = 0
        
    
    def get_tile_display_range(self):
        tiles_x = int(ceil(self.w/self.tileSize)) * (2 ** -self.zoom)
        tiles_y = int(ceil(self.h/self.tileSize)) * (2 ** -self.zoom)
        
        x0, y0 = self.pos_to_map_tile_int(self.map_focus)
        x_span = (tiles_x/2)+1
        y_span = (tiles_y/2)+1
        return 0,0,0,0
        return x0-x_span, y0-y_span, x0+x_span,  y0+y_span
    
    def set_map_focus(self, pos):
        self.map_focus = pos
        
    def set_map_origin(self, origin):
        self.origin = origin
        
    def gen_map(self):
        if self.inits_done == 0:
            self.tile_camera.reset(is_3d=False)
            self.tile_camera.position((self.cam_xoffset,self.cam_yoffset,0))
            self.inits_done = 1
        elif self.inits_done == 2:
            tile = self.tiles["0,0"]
            tile.texture._start(True)
            self.draw_home()
            tile.texture._end()
            self.inits_done = 3
            
    def update(self):
#        if self.inits_done == 1:
#            self.inits_done = 2
        return
        x0, y0, x1, y1 = self.get_tile_display_range()
        for x in range(x0,x1+1):
            for y in range(y0,y1+1):
                key = '[%d],[%di]', x ,y
                if not self.tiles.has_key(key):
                    new_tile = MapTile(shader=self.flatsh, map_camera=self.map_camera,  tilePixels=self.tileSize, tile_x=x, tile_y=y)
                    self.tiles[key] = new_tile
                    if (x==0) and (y==0):
                        new_tile.texture._start(False)
                        self.draw_home()
                        new_tile.texture._end()
        self.has_updated = True
                    
#    def drawMap(self):
    def draw(self, alpha=1):
        camera = self.map_camera
        camera.reset()
#        camera.position((self.xpos, self.ypos, 0))
        if self.inits_done == 1:
            self.inits_done = 2
            
        if self.inits_done >= 1:
            tile = self.tiles["0,0"]
#            tile.sprite.set_alpha(alpha)
#            tile.sprite.draw(self.flatsh, [tile.texture], camera=camera)
            tile.draw()
        return
#        camera = self.tile_camera
#        camera.reset(is_3d=False)
#        pix_pos = self.tile_pos_to_pix(self.map_focus)        
#        camera.position((pix_pos[0], pix_pos[1], 0))
        
        x0, y0, x1, y1 = self.get_tile_display_range()
        for x in range(x0,x1+1):
            for y in range(y0,y1+1):
                key = '[%d],[%di]', x ,y
                if self.tiles.has_key(key):
                    self.tiles[key].draw()
                    


    def pos_to_map_tile(self, pos):
        tile_x = (pos[0] * self.tile_scale)
        tile_y = (pos[1] * self.tile_scale)
        return [tile_x, tile_y]

    
    def pos_to_map_tile_int(self, pos):
        if pos is not None:
            tile_x, tile_y = self.pos_to_map_tile(pos)
            return int(tile_x), int(tile_y)
        
    def tile_pos_to_pix(self, pos):
        return [float(pos[0]*self.tileSize*self.tileResolution), float(pos[1]*self.tileSize*self.tileResolution)]
        
        
    def draw_home(self):
#        bar_shape = pi3d.Plane(camera=self.camera2d,  w=self.tileSize, h=self.tileSize)
#        bar_shape = pi3d.Plane(camera=self.camera2d,  w=100, h=100)
        bar_shape = pi3d.Plane(camera=self.tile_camera,  w=20, h=20)
        bar_shape.set_draw_details(self.matsh, [], 0, 0)
        bar_shape.set_material(self.home_colour)
        bar_shape.position( 0,  0, 5)
        bar_shape.draw()

        bar_shape.set_material((1.0, 0, 0))
        bar_shape.position( -self.tileSize*0.25,  -self.tileSize*0.25, 5)
        bar_shape.draw()

        bar_shape.set_material((0, 1.0, 0))
        bar_shape.position( self.tileSize*0.25,  self.tileSize*0.25, 5)
        bar_shape.draw()
    