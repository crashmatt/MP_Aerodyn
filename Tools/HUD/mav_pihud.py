#!/usr/bin/env python
'''
mav_pihud
mavlink connection for pi3d based HUD

Copyright Matthew Coleman
Released under the GNU GPL version 3 or later

Cutdown of mavproxy by Andrew Tridgell

'''

import sys, os, struct, math, time, socket
import fnmatch, errno, threading
import serial, Queue, select

from HUD import HUD
from multiprocessing import Queue


# find the mavlink.py module
for d in [ 'pymavlink',
           os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'MAVLink', 'pymavlink'),
           os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'MAVLink', 'mavlink', 'pymavlink') ]:
    if os.path.exists(d):
        sys.path.insert(0, d)


#for d in [ 'pymavlink',
#           os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'mavlink'),
#           os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'mavlink', 'pymavlink') ]:
#    if os.path.exists(d):
#

#sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'MAVlink', 'mavlink', 'pymavlink'))

#import select
#from modules.lib import textconsole
#from modules.lib import mp_settings

import mavlinkv10 as mavlink

class MPState(object):
    '''holds state of mavproxy'''
    def __init__(self):
        self.map = None
        self.status = MPStatus()

        # master mavlink device
        self.mav_master = None

    def master(self):
        '''return the currently chosen mavlink master object'''
#        if self.settings.link > len(self.mav_master):
#            self.settings.link = 1

        # try to use one with no link error
        return self.mav_master



class MPStatus(object):
    '''hold status information about the mavproxy'''
    def __init__(self):
        self.gps     = None
        self.msgs = {}
        self.msg_count = {}
        self.counters = {'MasterIn' : [], 'MasterOut' : 0, 'FGearIn' : 0, 'FGearOut' : 0, 'Slave' : 0}
        self.mav_error = 0
        self.target_system = 1
        self.target_component = 1

        self.exit = False
        self.flightmode = 'MAV'
        self.last_heartbeat = 0
        self.last_message = 0
        self.heartbeat_error = False
        
        self.have_gps_lock = False
        self.lost_gps_lock = False
        self.last_gps_lock = 0

        # Flag to sample home point
        self.home_set = False
        self.sample_home_time = 0
        self.home_lat = 0
        self.home_lon = 0

def cmd_link(args):
    for master in mpstate.mav_master:
        linkdelay = (mpstate.status.highest_msec - master.highest_msec)*1.0e-3
        if master.linkerror:
            print("link %u down" % (master.linknum+1))
        else:
            print("link %u OK (%u packets, %.2fs delay, %u lost, %.1f%% loss)" % (master.linknum+1,
                                                                                  mpstate.status.counters['MasterIn'][master.linknum],
                                                                                  linkdelay,
                                                                                  master.mav_loss,
                                                                                  master.packet_loss()))

def process_stdin(line):
    '''handle commands from user'''
    if line is None:
        sys.exit(0)
    line = line.strip()




def master_callback(m, master):
    '''process mavlink message m on master, sending any messages to recipients'''

    if getattr(m, '_timestamp', None) is None:
        master.post_message(m)
    mpstate.status.counters['MasterIn'][master.linknum] += 1

#    if getattr(m, 'time_boot_ms', None) is not None:
        # update link_delayed attribute
#        handle_msec_timestamp(m, master)

    mtype = m.get_type()
    msgtype = mtype
    msg = m
  
    if mtype in [ 'HEARTBEAT', 'GPS_RAW_INT', 'GPS_RAW', 'GLOBAL_POSITION_INT', 'SYS_STATUS' ]:
        if master.linkerror:
            master.linkerror = False
#            say("link %u OK" % (master.linknum+1))
        mpstate.status.last_message = time.time()
        master.last_message = mpstate.status.last_message

    if master.link_delayed:
        # don't process delayed packets that cause double reporting
        if mtype in [ 'MISSION_CURRENT', 'SYS_STATUS', 'VFR_HUD',
                      'GPS_RAW_INT', 'SCALED_PRESSURE', 'GLOBAL_POSITION_INT',
                      'NAV_CONTROLLER_OUTPUT' ]:
            return

    if mtype == 'HEARTBEAT':
        if (mpstate.status.target_system != m.get_srcSystem() or
            mpstate.status.target_component != m.get_srcComponent()):
            mpstate.status.target_system = m.get_srcSystem()
            mpstate.status.target_component = m.get_srcComponent()

        if mpstate.status.heartbeat_error:
            mpstate.status.heartbeat_error = False
        if master.linkerror:
            master.linkerror = False

        mpstate.status.last_heartbeat = time.time()
        master.last_heartbeat = mpstate.status.last_heartbeat

        set_hud_variable("mode", master.flightmode)
        
#        armed = mpstate.master().motors_armed()
#        if armed != mpstate.status.armed:
#            mpstate.status.armed = armed
        
#    elif mtype == 'STATUSTEXT':
#        if m.text != mpstate.status.last_apm_msg or time.time() > mpstate.status.last_apm_msg_time+2:
#            mpstate.console.writeln("APM: %s" % m.text, bg='red')
#            mpstate.status.last_apm_msg = m.text
#            mpstate.status.last_apm_msg_time = time.time()


    elif mtype == "SYS_STATUS":
#        battery_update(m)
        if master.flightmode != mpstate.status.flightmode:
            mpstate.status.flightmode = master.flightmode
#            mpstate.rl.set_prompt(mpstate.status.flightmode + "> ")

    elif msgtype == "VFR_HUD":
        have_gps_fix = False
        if 'GPS_RAW' in mpstate.status.msgs and mpstate.status.msgs['GPS_RAW'].fix_type == 2:
            have_gps_fix = True
        if 'GPS_RAW_INT' in mpstate.status.msgs and mpstate.status.msgs['GPS_RAW_INT'].fix_type == 3:
            have_gps_fix = True
        if have_gps_fix and not mpstate.status.have_gps_lock:
            if getattr(mpstate.status, "home_set", False) is False:
                mpstate.status.sample_home_time = time.time() + 10    
            mpstate.status.have_gps_lock = True
        
        set_hud_variable("heading", msg.heading)        
        set_hud_variable("groundspeed", msg.groundspeed)
        set_hud_variable("tas", msg.airspeed)


#    elif mtype == "GPS_RAW":
#            if m.fix_type != 2 and not mpstate.status.lost_gps_lock and (time.time() - mpstate.status.last_gps_lock) > 3:

    elif mtype == "GPS_RAW_INT":
        set_hud_variable("hdop", msg.eph)
        set_hud_variable("satellites", msg.satellites_visible)

        if mpstate.status.have_gps_lock:
            if m.fix_type != 3 and not mpstate.status.lost_gps_lock and (time.time() - mpstate.status.last_gps_lock) > 3:
                mpstate.status.lost_gps_lock = True
            if m.fix_type == 3 and mpstate.status.lost_gps_lock:
                mpstate.status.lost_gps_lock = False
            if m.fix_type == 3:
                mpstate.status.last_gps_lock = time.time()


    elif mtype == "NAV_CONTROLLER_OUTPUT" and mpstate.status.flightmode == "AUTO" and mpstate.settings.distreadout:
        rounded_dist = int(m.wp_dist/mpstate.settings.distreadout)*mpstate.settings.distreadout
        if math.fabs(rounded_dist - mpstate.status.last_distance_announce) >= mpstate.settings.distreadout:
#            if rounded_dist != 0:
#                say("%u" % rounded_dist, priority="progress")
            mpstate.status.last_distance_announce = rounded_dist

#    elif mtype == "FENCE_STATUS":
#        mpstate.status.last_fence_breach = m.breach_time
#        mpstate.status.last_fence_status = m.breach_status

    elif mtype == "GLOBAL_POSITION_INT":
#        report_altitude(m.relative_alt*0.001)
        vz = msg.vz   # vertical velocity in cm/s
        vz = float(vz) * -0.06  #vz from mm/s to meters/min
        set_hud_variable("vertical_speed", vz)
        
        if mpstate.status.sample_home_time != 0:
            if mpstate.status.last_heartbeat > mpstate.status.sample_home_time:
                mpstate.status.sample_home_time = 0
                mpstate.status.home_lat = msg.lat
                mpstate.status.home_lon = msg.lon
                mpstate.status.home_set = True
                
        if (mpstate.status.home_lat != 0) and (mpstate.status.home_lon != 0):
#            lat1 = mpstate.status.home_lat
#            lat2 = msg.lat
#            lon1 = mpstate.status.home_lon
#            lon2 = msg.lon           
            lat1 = math.radians(mpstate.status.home_lat)*1.0e-7
            lat2 = math.radians(msg.lat)*1.0e-7
            lon1 = math.radians(mpstate.status.home_lon)*1.0e-7
            lon2 = math.radians(msg.lon)*1.0e-7

            dLat = lat2 - lat1
            dLon = lon2 - lon1
            a = math.sin(0.5*dLat)**2 + math.sin(0.5*dLon)**2 * math.cos(lat1) * math.cos(lat2)
            c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0-a))
            distance = 6371 * 1000 * c
        
            set_hud_variable("home_dist", distance)
        
        #convert groundspeed to km/hr
#        groundspeed = math.sqrt((msg.vx*msg.vx) + (msg.vy*msg.vy) + (msg.vz*msg.vz)) * 0.0036
#        mpstate.hud_manager.set_variable("groundspeed", groundspeed)       
        set_hud_variable("agl", float(msg.relative_alt)*0.001)

    elif msgtype == "ATTITUDE":
        set_hud_variable("roll", math.degrees(msg.roll))
        set_hud_variable("pitch", math.degrees(msg.pitch))


    elif msgtype == "RAW_IMU":
        if(msg.zacc*msg.zacc > 100):
            slip = (180 / math.pi) * float(msg.yacc) / float(msg.zacc)
        else:
            slip = 0
        set_hud_variable("slip", slip)
         
    elif msgtype == "RC_CHANNELS_RAW":
        flap = msg.chan4_raw
        brake = msg.chan5_raw
        set_hud_variable("flap", flap)
        set_hud_variable("brake", brake)

    # keep the last message of each type around
    mpstate.status.msgs[m.get_type()] = m
    if not m.get_type() in mpstate.status.msg_count:
        mpstate.status.msg_count[m.get_type()] = 0
    mpstate.status.msg_count[m.get_type()] += 1



def set_hud_variable(var_name, value):
    try:
        mpstate.update_queue.put_nowait((var_name, value))
    except:
        print("Queue full")


def process_master(m):
    '''process packets from the MAVLink master'''
    try:
        s = m.recv()
    except Exception:
        return

    if m.first_byte and opts.auto_protocol:
        m.auto_mavlink_version(s)

    msgs = m.mav.parse_buffer(s)
    if msgs:
        for msg in msgs:
            if getattr(m, '_timestamp', None) is None:
                m.post_message(msg)

#===============================================================================
#             
#             msgtype = msg.get_type()
# 
# 
#             if msgtype == "HEARTBEAT":              
#                 
#                 set_hud_variable("mode", m.)
#                     
#             elif msgtype == "GLOBAL_POSITION_INT":
#                 vz = msg.vz   # vertical velocity in cm/s
#                 vz = float(vz) * -0.06  #vz from mm/s to meters/min
#                 set_hud_variable("vertical_speed", vz)
#         
#                 #convert groundspeed to km/hr
#         #        groundspeed = math.sqrt((msg.vx*msg.vx) + (msg.vy*msg.vy) + (msg.vz*msg.vz)) * 0.0036
#         #        mpstate.hud_manager.set_variable("groundspeed", groundspeed)
#                 
#                 set_hud_variable("agl", float(msg.relative_alt)*0.001)
#                 
#                 
#             elif msgtype == "VFR_HUD":
#                 set_hud_variable("heading", msg.heading)
#                 
#                 set_hud_variable("groundspeed", msg.groundspeed)
#                 set_hud_variable("tas", msg.airspeed)
#         
#             elif msgtype == "ATTITUDE":
#                 set_hud_variable("roll", math.degrees(msg.roll))
#                 set_hud_variable("pitch", math.degrees(msg.pitch))
#         
#             elif msgtype == "GPS_RAW_INT":
#                 set_hud_variable("hdop", msg.eph)
#                 set_hud_variable("satellites", msg.satellites_visible)
#                 
#             elif msgtype == "RAW_IMU":
#                 if(msg.zacc*msg.zacc > 100):
#                     slip = (180 / math.pi) * float(msg.yacc) / float(msg.zacc)
#                 else:
#                     slip = 0
#                 set_hud_variable("slip", slip)
#                 
#             elif msgtype == "RC_CHANNELS_RAW":
#                 flap = msg.chan4_raw
#                 brake = msg.chan5_raw
#                 set_hud_variable("flap", flap)
#                 set_hud_variable("brake", brake)
#===============================================================================
                
#            elif msgtype == "GLOBAL_POSITION_INT":
#                msg.
#            else:
#                print msgtype
                
                
            elif msgtype == "VFR_HUD":
                set_hud_variable("heading", msg.heading)
                
                set_hud_variable("groundspeed", msg.groundspeed)
                set_hud_variable("tas", msg.airspeed)
        
            elif msgtype == "ATTITUDE":
                set_hud_variable("roll", math.degrees(msg.roll))
                set_hud_variable("pitch", math.degrees(msg.pitch))
        


def check_link_status():
    '''check status of master links'''
    tnow = time.time()
    if mpstate.status.last_message != 0 and tnow > mpstate.status.last_message + 5:
#        say("no link")
        mpstate.status.heartbeat_error = True
    for master in mpstate.mav_master:
        if not master.linkerror and tnow > master.last_message + 5:
#            say("link %u down" % (master.linknum+1))
            master.linkerror = True


def main_loop():
    '''main processing loop'''
    if not opts.nowait and not mpstate.status.exit:
        mpstate.mav_master.wait_heartbeat()
            
    master = mpstate.mav_master
    while True:
        if mpstate is None or mpstate.status.exit:
            return

        if master.fd is None:
            if master.port.inWaiting() > 0:
                process_master(master)
        else:
            process_master(master)
            
                
        time.sleep(0.01)





#------------------------------------------------------------- def input_loop():
    #------------------------------------------------- '''wait for user input'''
    #--------------------------------------------------------------- while True:
        #------------------------------------ while mpstate.rl.line is not None:
            #-------------------------------------------------- time.sleep(0.01)
        #------------------------------------------------------------------ try:
            #------------------------------- line = raw_input(mpstate.rl.prompt)
        #------------------------------------------------------ except EOFError:
            #---------------------------------------- mpstate.status.exit = True
            #------------------------------------------------------- sys.exit(1)
        #------------------------------------------------ mpstate.rl.line = line



if __name__ == '__main__':

    from optparse import OptionParser
    parser = OptionParser("mavproxy.py [options]")

    parser.add_option("--master",dest="master", help="MAVLink master port", default=[])
    parser.add_option("--baudrate", dest="baudrate", type='int',
                      help="master port baud rate", default=115200)
    parser.add_option("--out",   dest="output", help="MAVLink output port",
                      action='append', default=[])
    parser.add_option("--source-system", dest='SOURCE_SYSTEM', type='int',
                      default=255, help='MAVLink source system for this GCS')
    parser.add_option("--target-system", dest='TARGET_SYSTEM', type='int',
                      default=1, help='MAVLink target master system')
    parser.add_option("--target-component", dest='TARGET_COMPONENT', type='int',
                      default=1, help='MAVLink target master component')
    parser.add_option("--nodtr", dest="nodtr", help="disable DTR drop on close",
                      action='store_true', default=False)
    parser.add_option("--aircraft", dest="aircraft", help="aircraft name", default=None)
    parser.add_option(
        '--load-module',
        action='append',
        default=[],
        help='Load the specified module. Can be used multiple times, or with a comma separated list')
    parser.add_option("--mav09", action='store_true', default=False, help="Use MAVLink protocol 0.9")
    parser.add_option("--auto-protocol", action='store_true', default=False, help="Auto detect MAVLink protocol version")
    parser.add_option("--nowait", action='store_true', default=False, help="don't wait for HEARTBEAT on startup")

    (opts, args) = parser.parse_args()

    if opts.mav09:
        os.environ['MAVLINK09'] = '1'
    import mavutil, mavwp, mavparm

    # global mavproxy state
    mpstate = MPState()
    mpstate.status.exit = False

    if not opts.master:
        serial_list = mavutil.auto_detect_serial(preferred_list=['*FTDI*',"*Arduino_Mega_2560*", "*3D_Robotics*", "*USB_to_UART*"])
        if len(serial_list) == 1:
            opts.master = [serial_list[0].device]
        else:
            print('''
Please choose a MAVLink master with --master
For example:
    --master=com14
    --master=/dev/ttyUSB0
    --master=127.0.0.1:14550

Auto-detected serial ports are:
''')
            for port in serial_list:
                print("%s" % port)
            sys.exit(1)

    # container for status information
    mpstate.status.target_system = opts.TARGET_SYSTEM
    mpstate.status.target_component = opts.TARGET_COMPONENT

    mpstate.mav_master = []

    # open master link
    mdev = opts.master
    if mdev.startswith('tcp:'):
        m = mavutil.mavtcp(mdev[4:])
    elif mdev.find(':') != -1:
        m = mavutil.mavudp(mdev, input=True)
    else:
        m = mavutil.mavserial(mdev, baud=opts.baudrate, autoreconnect=True)
    m.mav.set_callback(master_callback, m)
    m.linknum = len(mpstate.mav_master)
    m.linkerror = False
    m.link_delayed = False
    m.last_heartbeat = 0
    m.last_message = 0
    m.highest_msec = 0
    mpstate.mav_master = m
    mpstate.status.counters['MasterIn'].append(0)

    mpstate.update_queue = Queue(100)
    mpstate.hud = HUD(master=True, update_queue=mpstate.update_queue)

    # run main loop as a thread
    mpstate.status.thread = threading.Thread(target=main_loop)
    mpstate.status.thread.daemon = True
    mpstate.status.thread.start()
    
    time.sleep(1.0)
    
    mpstate.hud.run_hud()
    
#    mpstate.status.exit = True
#    mpstate.status.thread.join()

    # use main program for input. This ensures the terminal cleans
    # up on exit
    #---------------------------------------------------------------------- try:
        #---------------------------------------------------------- input_loop()
    #------------------------------------------------- except KeyboardInterrupt:
        #------------------------------------------------------ print("exiting")
        #-------------------------------------------- mpstate.status.exit = True
        #----------------------------------------------------------- sys.exit(1)
