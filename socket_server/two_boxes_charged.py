#%%
import random
import math
import numpy as np
import csv

#import sys
#import logging
#logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

from socket_server import Server

server = Server('127.0.0.1', 10004)
server.setup()
server.start()

import subprocess
try:
    clientA = subprocess.Popen(['/home/ml/espresso/build/pypresso', 'esp_client_charged.py', '20'])
    clientB = subprocess.Popen(['/home/ml/espresso/build/pypresso', 'esp_client_charged.py', '40'])
except:
    server.server_socket.close()

#wait for clients to connect
while len(server.addr_list)<3:
    pass

l_bjerrum = 7.0
temp = 1
N1 = 80
N2 = 10


for i in range(int(N1/2)):
    server.request("system.part.add(pos=system.box_l * np.random.random(3), type = 0, q = -1.0)", 0, wait = False)
    server.request("system.part.add(pos=system.box_l * np.random.random(3), type = 1, q = +1.0)", 0, wait = False)

for i in range(int(N2/2)):
    server.request("system.part.add(pos=system.box_l * np.random.random(3), type = 0, q = -1.0)", 1, wait = False)
    server.request("system.part.add(pos=system.box_l * np.random.random(3), type = 1, q = +1.0)", 1, wait = False)

server.request("system.thermostat.set_langevin(kT=1, gamma=1, seed=42)",0, wait = False)
server.request("system.thermostat.set_langevin(kT=1, gamma=1, seed=42)",1, wait = False)
server.request(["system.minimize_energy.init(f_max=50, gamma=30.0, max_steps=10000, max_displacement=0.001)",
                "system.minimize_energy.minimize()"],0, wait = False)    
server.request(["system.minimize_energy.init(f_max=50, gamma=30.0, max_steps=10000, max_displacement=0.001)",
                "system.minimize_energy.minimize()"],1, wait = False)        



server.request(
        [
        "system.non_bonded_inter[0, 0].lennard_jones.set_params(epsilon=1, sigma=1, cutoff=3, shift='auto')",
        "system.non_bonded_inter[0, 1].lennard_jones.set_params(epsilon=1, sigma=1, cutoff=3, shift='auto')"
        "system.non_bonded_inter[1, 1].lennard_jones.set_params(epsilon=1, sigma=1, cutoff=3, shift='auto')"
        ], 
        0, wait = False
    )
server.request(
        [
        "system.non_bonded_inter[0, 0].lennard_jones.set_params(epsilon=1, sigma=1, cutoff=3, shift='auto')",
        "system.non_bonded_inter[0, 1].lennard_jones.set_params(epsilon=1, sigma=1, cutoff=3, shift='auto')"
        "system.non_bonded_inter[1, 1].lennard_jones.set_params(epsilon=1, sigma=1, cutoff=3, shift='auto')"
        ], 
        1, wait = False
    )

print(server.request("system.analysis.energy()",0))
print(server.request("system.analysis.energy())",1))
print(server.request("len(system.part[:].id)",0))
# %%
print(server.request("system.box_l",1))
# %%
server.request(f"system.actors.add(electrostatics.P3M(prefactor={l_bjerrum * temp},accuracy=1e-3))",0)
# %%
