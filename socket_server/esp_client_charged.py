#%%
import random
import sys
import espressomd
from espressomd import electrostatics
import numpy as np

import argparse

parser = argparse.ArgumentParser(description='box_length')
parser.add_argument('l',
                       metavar='l',
                       type=float,
                       help='box_length')

args = parser.parse_args()

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


required_features = ["EXTERNAL_FORCES", "MASS", "ELECTROSTATICS", "WCA"]
espressomd.assert_features(required_features)
box = np.array([args.l, args.l, args.l])
system = espressomd.System(box_l=box)
system.time_step = 0.0005
system.cell_system.set_domain_decomposition(use_verlet_lists=True)
system.cell_system.skin = 0.4
#%%
class EspressoClient(BaseClient):
    from espressomd import electrostatics
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
            except:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                self.logger.debug(exc_type, exc_value, exc_traceback)
            return result
        if isinstance(request, str):
            return get_result(request)
        elif isinstance(request, list):
            result =[]
            for item in request:
                result.append(get_result(item))
            return result
         
client = EspressoClient('127.0.0.1', 10004)
client.system = system
client.start()
# %%
while client.connected:
    pass

client.logger.debug("An error occurred")