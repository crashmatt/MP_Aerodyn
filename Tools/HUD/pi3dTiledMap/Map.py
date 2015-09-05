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
        
        self.home_colour = (1.0, 0.2, 1.0, 0.8)
        self.marker_colour = (1.0, 0.2, 1.0, 0.8)
        
        # camera for viewing the map. Owned by the track since it can move
        self.map_camera = pi3d.Camera(is_3d = False)

        # 2d camera for drawing on the map tiles
        self.tile_camera = pi3d.Camera(is_3d=False)    #pi3d.Camera(is_3d=False)

        # shader for drawing the map        
#        self.flatsh = pi3d.Shader("uv_flat")
        
        #shader for drawing simple colour shapes on the map
        self.matsh = pi3d.Shader("mat_flat")
        
        
        self.point_shader = pi3d.Shader(vshader_source = """
precision mediump float;
attribute vec3 vertex;
uniform mat4 modelviewmatrix[2];
uniform vec3 unib[4];
varying float dist;

void main(void) {
  gl_Position = modelviewmatrix[1] * vec4(vertex.xy, 20.0, 1.0);
  gl_PointSize = unib[2][2];
  dist = length(gl_Position.xy);
}
""",
fshader_source = """
precision mediump float;
uniform vec3 unib[4];
uniform vec3 unif[20];
varying float dist;

void main(void) {
  gl_FragColor = vec4(unib[1], 1.0);
  gl_FragColor.a = clamp(1.2-dist, 0.1, 0.8) * unif[5][2];
                      
}
""")

        self.screen_width = Display.INSTANCE.width
        self.screen_height = Display.INSTANCE.height
               
#        self.home = pi3d.Plane(camera=self.tile_camera,  w=20, h=20, z=5.8)
#        self.home.set_draw_details(self.matsh, [], 0, 0)
#        self.home.set_material(self.home_colour)
#        self.home.set_alpha(alpha)
        
        self.home_pointer = pi3d.Lines(camera=self.tile_camera, vertices=[[0, self.screen_height*0.3, 1.0],[0, self.screen_height*0.35, 1.0]], z=5.9, line_width=6)
        self.home_pointer.set_draw_details(self.matsh, [], 0, 0)
        self.home_pointer.set_material(self.marker_colour)
        self.home_pointer.set_alpha(alpha)
        
        ppc = 80    #points per circle
        circles = 10
        circle_points = np.zeros((ppc*circles,3), dtype=np.float)
        rad_per_point = 2 * pi / ppc
        for circle in range (0,circles):
            if circle == 0:
                radius = 20.0
                delta_deg = 1 / radius
            else:
                radius = circle * 150.0
                delta_deg = 3 / radius
            
            for i in range(0,ppc):
                index = (ppc*(circle-1)) + i
                if i%2 == 0:
                    deg = i * 2 * pi / ppc
                    deg = deg + delta_deg
                else:
                    deg = (i-1) * 2 * pi / ppc
                    deg = deg - delta_deg
                circle_points[index,0] = radius * sin(deg)
                circle_points[index,1] = radius * cos(deg)
                circle_points[index,2] = 5.7         
               
        self.distance_radius = pi3d.Lines(camera=self.tile_camera, vertices=circle_points, z=5.7, line_width=3, closed=True)
        self.distance_radius.set_line_width(3, strip=False)
        #self.distance_radius = pi3d.Points(camera=self.map_camera, vertices=circle_points, z=5.7, point_size=6)
        self.distance_radius.set_draw_details(self.point_shader, [], 0, 0)
        self.distance_radius.set_material(self.marker_colour)
        self.distance_radius.set_alpha(0.8)
                
        #---------------- dist_spot_points = np.zeros((22*22,3), dtype=np.float)
        #----------------------------------------------- for x in range (0, 21):
            #------------------------------------------- for y in range (0, 21):
                #-------------------------------------------- index = (x*21) + y
                #---------------------- dist_spot_points[index,0] = (x-10)*200.0
                #---------------------- dist_spot_points[index,1] = (y-10)*200.0
                #------------------------------- dist_spot_points[index,2] = 5.6
        # self.distance_spots = pi3d.Points(camera=self.map_camera, vertices=dist_spot_points, z=5.7, point_size=10)
        #----- self.distance_spots.set_draw_details(self.point_shader, [], 0, 0)
        #------------------ self.distance_spots.set_material(self.marker_colour)
        #----------------------------------- self.distance_spots.set_alpha(0.75)
        
        self.track = np.zeros((2000,3), dtype=np.float)
        self.track_index = 0
        self.track_sprite = pi3d.Points(camera=self.map_camera, vertices=self.track, point_size=self._track_width, z=30.0)
        #self.track_sprite = pi3d.Lines(camera=self.map_camera, vertices=self.track, line_width=self._track_width)

        self.trackshader = pi3d.Shader(vshader_source = """
precision mediump float;
attribute vec3 vertex;
uniform mat4 modelviewmatrix[2];
uniform vec3 unib[4];
varying vec4 colour;

void main(void) {

  gl_Position = modelviewmatrix[1] * vec4(vertex, 1.0);
  colour = vec4(cos((vertex.z*2.094) - 2.094), cos(vertex.z*2.094), cos((vertex.z*2.094) + 2.094), 1.0 ); 
  colour.a = clamp(1.5 - length(gl_Position.xy), 0.1, 0.8) ;

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

        colour = self._climbrate * (1.0/25.0)
        if colour < 0.0:
            colour = -sqrt(-colour)
        else:
            colour = sqrt(colour)
            
        if colour > 1.0:
            colour = 1.0
        if colour < -1.0:
            colour = -1.0
        
        self.track[self.track_index] = [self._aircraft_pos.x, self._aircraft_pos.y, colour]
        
        self.track_sprite.scale(self._zoom, self._zoom, 1.0)
        if (self._zoom > 1.0):
            self.track_sprite.set_point_size(self._track_width * self._zoom)
        else:
            self.track_sprite.set_point_size(self._track_width)
        
#        self.track_sprite.position(-self._aircraft_pos.x * self._zoom, -self._aircraft_pos.y * self._zoom, 7.0)
        
        b = self.track_sprite.buf[0]
        b.re_init(self.track, offset=0)
        
        self.track_index = (self.track_index + 1) % len(self.track)
          
        self._last_aircraft_pos = self._aircraft_pos


    def draw(self):
#        self.track_sprite.set_line_width(self._track_width, False, False)
        self.track_sprite.position(-self._aircraft_pos.x * self._zoom, -self._aircraft_pos.y * self._zoom, 30.0)
        self.track_sprite.draw()

        #-------------------------- self.home.scale(self._zoom, self._zoom, 1.0)
        # self.home.position( -self._aircraft_pos.x*self._zoom,  -self._aircraft_pos.y*self._zoom, 5.9)
        #------------------------------------------------------ self.home.draw()
        
        rot = degrees(atan2(self._aircraft_pos.x, -self._aircraft_pos.y))
        self.home_pointer.set_line_width(10.0, False, False)
        self.home_pointer.rotateToZ(rot)
        self.home_pointer.draw()
        
        #---------------- self.distance_spots.scale(self._zoom, self._zoom, 1.0)
        # self.distance_spots.position( -self._aircraft_pos.x*self._zoom,  -self._aircraft_pos.y*self._zoom, 5.9)
        #-------------------------------------------- self.distance_spots.draw()
        
        self.distance_radius.set_line_width(3.0, False, False)
        self.distance_radius.scale(self._zoom, self._zoom, 1.0)
        self.distance_radius.position( -self._aircraft_pos.x*self._zoom,  -self._aircraft_pos.y*self._zoom, 7.0)
        self.distance_radius.draw()
        return
                    
