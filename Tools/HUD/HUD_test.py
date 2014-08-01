'''
Created on 31 Jul 2014

@author: matt
'''
from multiprocessing import Process, Queue

from HUD import HUD

if __name__ == '__main__':
    Q = Queue(100)
    Q.put_nowait(("roll", 30))
    Q.put_nowait(("pitch", 5))
    hud = HUD(simulate=False, master=True, update_queue=Q)
    hud.run_hud()    