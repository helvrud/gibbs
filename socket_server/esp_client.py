#%%
import random
import sys
import espressomd
import numpy as np

from socket_server import BaseClient
#from socket_server.Client2 import ErrorRequest

#import logging
#import sys
#logging.basicConfig(stream=open('log', 'w'), level=logging.DEBUG)

box = np.array([10, 10, 10])
system = espressomd.System(box_l=box)
system.time_step = 0.0005
system.cell_system.set_domain_decomposition(use_verlet_lists=True)
system.cell_system.skin = 0.4

system.non_bonded_inter[0, 0].lennard_jones.set_params(
    epsilon=1.0, sigma=1.0,
    cutoff=3.0, shift="auto")
#%%
class EspressoClient(BaseClient):
    system = None
    def handle_request(self, request):
        try:
            self.logger.debug(f'eval({request})')
            result = eval(request)
        except Exception as e:
            self.logger.debug(e)
            result = e
        return result
         
client = EspressoClient('127.0.0.1', 10000)
client.system = system
client.start()
# %%
while client.connected:
    pass