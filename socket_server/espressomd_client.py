#%%
import sys
import espressomd
import numpy as np

from socket_server import Client

box = np.array([40, 30, 20])
system = espressomd.System(box_l=box)
system.time_step = 0.0005
system.cell_system.set_domain_decomposition(use_verlet_lists=True)
system.cell_system.skin = 0.4

system.non_bonded_inter[0, 0].lennard_jones.set_params(
    epsilon=100.0, sigma=1.0,
    cutoff=3.0, shift="auto")
#%%
class EspressoClient(Client):
    system = None
    #method eval has to be overridden, 
    #so that you can use import from this script
    #otherwise you will get NameError trying to eval(np.*)
    def eval(self, eval_str):
        result = eval(eval_str)
        return result

client = EspressoClient('127.0.0.1', 10001)
client.system = system
client.connect()
client.loop()

# %%
