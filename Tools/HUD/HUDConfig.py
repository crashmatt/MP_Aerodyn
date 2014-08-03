'''
Created on 23 Jul 2014

@author: matt
'''

import json

class layerSetup(object):
    def __init__(self, name):
        self.name = name
        self.update_on_phase = None
        self.update_timestep = 0
        self.update_at_start = False
        self.force_redraw = False

class HUDConfig(object):
    '''
    classdocs
    '''

    def __init__(self, HUD):
        '''
        Constructor
        '''
        self.filename = "HUD.cfg"
        self.layerConfigs = []
        self.variables = []
        
    def get_layers(self):
        return self.layers
    
    def store_hud_config(self):
        config = ConfigParser.ConfigParser()
        config.add_section("static_layer")
        
        with open('hud.cfg', 'wb') as configfile:
            config.write(configfile)    