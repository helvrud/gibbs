#%%
import random
import sys
import espressomd
import numpy as np

REGEX_POST_PROCESS = True
LOGGING = False

if REGEX_POST_PROCESS:
    import re
    PATTERN = re.compile(r'(?<![a-zA-Z0-9._])system(?![a-zA-Z0-9_])')

from socket_server import BaseClient

if  LOGGING:
    import logging
    import sys
    logging.basicConfig(stream=open('log', 'w'), level=logging.DEBUG)

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
        def get_result(request_item):
            try:
                request_item = PATTERN.sub(r'self.system', request_item)
                self.logger.debug(f'eval({request_item})')
                result = eval(request_item)
            except Exception as e:
                self.logger.debug(e)
                result = e
            return result
        if isinstance(request, str):
            return get_result(request)
        elif isinstance(request, list):
            result =[]
            for item in request:
                result.append(get_result(item))
            return result
         
client = EspressoClient('127.0.0.1', 10000)
client.system = system
client.start()
# %%
while client.connected:
    pass