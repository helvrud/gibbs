#%%
import espressomd
import numpy as np

from socket_server import Client

box = np.array([40, 30, 20])
system = espressomd.System(box_l=box)

class EspressoClient(Client):
    system = None
    #method eval has to be overridden, 
    #so that you can use import from this script
    #otherwise you will get NameError trying to eval(np.*)
    def eval(self, eval_str):
        result = eval(eval_str)
        return result

client = EspressoClient('127.0.0.1', 10000)
client.system = system
client.connect()
client.loop()