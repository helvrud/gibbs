#%%
import random
import math
import matplotlib.pyplot as plt
import numpy as np

import pandas as pd
import socket_nodes
import tqdm
#os.chdir(sys.path[0])
import threading
from socket_nodes import Server
import logging
logging.basicConfig(stream=open('log_server', 'w'), level=logging.INFO)
from monte_carlo import MonteCarloSocketNodes
#%%
#params
ELECTROSTATIC = False

V_all = 40**3*2
v = 0.5 #relative volume of the box with fixed anions
#box volumes and dimmensions
V = [V_all*(1-v),V_all*v]
box_l = [V_**(1/3) for V_ in V]
l_bjerrum = 2.0
temp = 1

###start server and nodes
server = socket_nodes.utils.create_server_and_nodes(
    scripts = ['esp_node.py', 'esp_node.py'], 
    args_list=[[str(l_)] for l_ in box_l], 
    python_executable = 'python')
#%%
def populate_system(n1, n2, n_fixed):
    ##populate the systems##
    server(f"/populate({int(n1/2)}, type = 0, q = -1.0)", 0)
    server(f"/populate({int(n1/2)}, type = 1, q = +1.0)", 0)

    server(f"/populate({int(n2/2)}, type = 0, q = -1.0)", 1)
    server(f"/populate({int(n2/2)}, type = 1, q = +1.0)", 1)

    server(f"/populate({int(n_fixed)}, type = 2, q = -1.0)", 1)
    server(f"/populate({int(n_fixed)}, type = 1, q = +1.0)", 1)
N1 = 150
N2 = 50
N_anion_fixed = 0
populate_system(N1, N2, N_anion_fixed)
#%%
def setup_system():
    ##add LJ interactions and thermostats### 
    server(
            [
            "system.non_bonded_inter[0, 0].lennard_jones.set_params(epsilon=1, sigma=1, cutoff=3, shift='auto')",
            "system.non_bonded_inter[0, 1].lennard_jones.set_params(epsilon=1, sigma=1, cutoff=3, shift='auto')",
            "system.non_bonded_inter[1, 1].lennard_jones.set_params(epsilon=1, sigma=1, cutoff=3, shift='auto')",
            "system.non_bonded_inter[0, 2].lennard_jones.set_params(epsilon=1, sigma=1, cutoff=3, shift='auto')",
            "system.non_bonded_inter[1, 2].lennard_jones.set_params(epsilon=1, sigma=1, cutoff=3, shift='auto')",
            "system.non_bonded_inter[2, 2].lennard_jones.set_params(epsilon=1, sigma=1, cutoff=3, shift='auto')",
            "system.__setattr__('time_step', 0.001)",
            "system.cell_system.__setattr__('skin', 0.4)",
            "system.thermostat.set_langevin(kT=1, gamma=1, seed=42)",
            "system.minimize_energy.init(f_max=50, gamma=30.0, max_steps=10000, max_displacement=0.001)",
            "system.minimize_energy.minimize()"
            ], 
            [0,1]
        )

    ##switch on electrostatics
    if ELECTROSTATIC:
        server.request(f"system.actors.add(espressomd.electrostatics.P3M(prefactor={l_bjerrum * temp},accuracy=1e-3))",[0,1])

    #minimize energy and run md
    server([
                "system.minimize_energy.init(f_max=50, gamma=30.0, max_steps=10000, max_displacement=0.001)",
                "system.minimize_energy.minimize()",
                f"system.integrator.run({10000})"
                ],
                [0,1]
            )
setup_system()
#%%
mc = MonteCarloSocketNodes(server)
# %%
for i in range(1000):
    print(mc.step()['n_mobile'])
# %%
mc.current_state
# %%
mc.step()
# %%
