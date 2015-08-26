'''
Created on 16 Jul 2015

@author: matt
'''

import pi3d
from pi3d.util.OffScreenTexture import OffScreenTexture
from pi3d.shape.FlipSprite import FlipSprite
from MapTile import MapTile
from _dbus_bindings import String
from math import sin, cos, log , pi, ceil, floor, atan2, degrees, fabs, sqrt
from Lines2d import Lines2d
import colorsys
from pi3dTiledMap import CoordSys
from pi3dTiledMap.CoordSys import Cartesian
#from gi.overrides.keysyms import careof
import time
import numpy as np


class Map(object):
    '''
    A tiled map system running under pi3d.  Organises and draws small parts of a map (tiles) from a larger collection. 
    '''


    def __init__(self, w, h, z, resolution=1, alpha = 1.0):
        '''
        resolution = pixels per meter (not supported yet)
        w = Pixel height to show
        h = Pixel width to show
        z = Map stack depth
        alpha = transparency
        '''        
        from pi3d.Display import Display

        self.w = w
        self.h = h
        self.z = z
        self.alpha = alpha

        self._zoom_target = 1.0
        self._zoom_rate = 1.0
        self._zoom = 1.0
        self._track_width = 5
   
        self._map_focus         = CoordSys.Cartesian(0.0,0.0)
        self._aircraft_pos      = CoordSys.Cartesian(0.0,0.0)
        self._last_aircraft_pos = CoordSys.Cartesian(0.0,0.0)
        
        self._climbrate = 0.0

        self._last_update_time = time.time()
        
        self.home_colour = (0.2, 0.2, 1.0, 0.6)
        self.marker_colour = (0.2, 0.2, 1.0, 0.6)
        
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
        
#        self.cam_xoffset = (self.screen_width-tileSize) * 0.5
#        self.cam_yoffset = (self.screen_height-tileSize) * 0.5
        
        self.map_texture = OffScreenTexture(name="map_texture", w=self.screen_width, h=self.screen_height)
        self.map_sprite = FlipSprite(camera=self.tile_camera, w=self.screen_width, h=self.screen_height, z=6.0, flip=True)
        
        self.track = np.zeros((2000,3), dtype=np.float)
        self.track_index = 0
        self.track_sprite = pi3d.Points(camera=self.map_camera, vertices=self.track, point_size=self._track_width)
#        self.track_sprite = pi3d.Lines(camera=self.map_camera, vertices=self.track, line_width=self._track_width)
        
        self.trackshader = pi3d.Shader(vshader_source = """

precision mediump float;
attribute vec3 vertex;
uniform mat4 modelviewmatrix[2];
uniform vec3 unib[4];
varying vec4 colour;

void main(void) {

  gl_Position = modelviewmatrix[1] * vec4(vertex, 1.0);
  colour = mix(mix(vec4(0.0, 0.0, 1.0, 1.0), vec4(0.0, 1.0, 0.0, 1.0),
                clamp(vertex.z * 2.0 - 1.0, 0.0, 1.0)),
                  vec4(1.0, 0.0, 0.0, 1.0),
                    clamp(1.0 - vertex.z * 2.0, 0.0, 1.0));
  colour.a = 1.5 - length(gl_Position.xy);

  gl_PointSize = unib[2][2];
}
""",
fshader_source = """
precision mediump float;

varying vec4 colour;

void main(void) {
  gl_FragColor = colour;
}
""")
        self.track_sprite.set_shader(self.trackshader)
        
    def set_zoom_target(self,zoom, rate):
        self._zoom_target = zoom
        self._zoom_rate = rate
    
    
    # set the map focus in relative position from origin [x, y]
    def set_map_focus(self, pos):
        self._map_focus = pos
        
    def set_map_origin(self, origin):
        self._origin = origin

    def set_aircraft_pos(self, pos):
        self._aircraft_pos = pos
        
    def set_climbrate(self, climbrate):
        self._climbrate = climbrate
            
        
    def gen_map(self):
        self._update_zoom()


    def _update_zoom(self):
        now = time.time()
        deltaT = now - self._last_update_time
        deltaZ = self._zoom_target - self._zoom
        deltaZ = deltaZ * (deltaT * self._zoom_rate)
        self._zoom = self._zoom + deltaZ
        self._last_update_time = now
        
                    
    def interpolate_ratio(self, ratio, y1, y2):
        delta = y2 - y1
        return (ratio * delta) + y1
        
    def interpolate(self, x, x1, x2, y1, y2):
        deltax = x2 - x1
        ratio = (x - x1) / deltax
        deltay = y2 - y1
        return (ratio * deltay) + y1
            
            
    def get_rate_colour(self, rate):
        colour = (1.0, 1.0, 1.0, 1.0)

        if(rate <= -20):
            colour = (0.0, 0.0, 1.0)
        elif(rate >= 20):
            colour = (1.0, 0.0, 0.0)
        else:
            hue = 0.333
            if rate >= 0:
                hue = self.interpolate(rate, 0, 20, 0.333, 0.0)
            else:
                hue = self.interpolate(rate, 0, -20, 0.666, 0.0)
            colour = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        return colour

    def set_tile_alpha(self, tile, distance):
        alpha = self.interpolate(distance, 1.0, 1.9, 1.0, 0.1)
        if alpha < 0.0:
            alpha = 0.0
        elif alpha > self.alpha:
            alpha = self.alpha
        tile.set_alpha(alpha)
                    
    def add_segment(self):
        if self._last_aircraft_pos == self._aircraft_pos:
            return

#        self.track.append((self._aircraft_pos.x, self._aircraft_pos.y, 0.5))
        colour = self._climbrate * (-0.5 / 15.0) + 0.5
        if colour > 1.0:
            colour = 1.0
        if colour < 0:
            colour = 0
        
        self.track[self.track_index] = [self._aircraft_pos.x, self._aircraft_pos.y, colour]
        
        self.track_sprite.scale(self._zoom, self._zoom, 1.0)
        if (self._zoom > 1.0):
            self.track_sprite.set_point_size(self._track_width * self._zoom)
        else:
            self.track_sprite.set_point_size(self._track_width)
        
        self.track_sprite.position(-self._aircraft_pos.x * self._zoom, -self._aircraft_pos.y * self._zoom, 6.0)
        
        b = self.track_sprite.buf[0]
        b.re_init(self.track, offset=0)
        
        self.track_index = (self.track_index + 1) % len(self.track)
        
#        self.map_texture._start(True)
#        self.track_sprite.position(self._aircraft_pos.x-self.track_sprite.x(), self._aircraft_pos.y-self.track_sprite.y(), 0.0)
#        self.track_sprite.draw()
#        self.map_texture._end()
  
        self._last_aircraft_pos = self._aircraft_pos


    def draw(self):
#        camera = self.map_camera
#        camera.reset(is_3d=False, scale=self._zoom)
#        tileCoord = CoordSys.TileCoord(cartesian=self._map_focus, tileSize=self.tileSize)
#        pxlPos = tileCoord.get_abs_pixel_pos(self.tileSize)
#        camera.position((self._map_focus.x,self._map_focus.y, 0.0))

#        self.map_sprite.set_draw_details(self.flatsh, [self.map_texture])
#        self.map_sprite.draw()
        self.track_sprite.draw()
        
        return
                    

#===============================================================================
#     def _draw_home(self):
# #        bar_shape = pi3d.Plane(camera=self.camera2d,  w=100, h=100)
#         bar_shape = pi3d.Plane(camera=self.tile_camera,  w=20, h=20)
#         bar_shape.set_draw_details(self.matsh, [], 0, 0)
#         bar_shape.set_material(self.home_colour)
#         bar_shape.position( 0,  0, 5)
#         bar_shape.draw()
#         
#     def _draw_tile_markers(self, tilenum):
#         if tilenum.tile_num_x == 0 and tilenum.tile_num_y == 0 :
#             self._draw_home()
#             return
#         
#         points = ((15,-15), (0,0), (15,15))
#         
#         thickness = 5
#         rot = atan2(tilenum.tile_num_y, tilenum.tile_num_x)
#         rot = degrees(rot) # - 45
#         
#         marker = Lines2d(camera=self.tile_camera, points=points, line_width=thickness, material=self.marker_colour, z=6.0, rz=rot)
#         marker.set_draw_details(self.matsh, [], 0, 0)
#         marker.draw()
#     
#===============================================================================