#%%
from shared_data import *
from socket_nodes import Server
import socket_nodes
from monte_carlo import MonteCarloSocketNodes

import random
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tqdm
import threading
PAIR = [0,1]
SIDES = [0,1]

###start server and nodes
server = socket_nodes.utils.create_server_and_nodes(
    scripts = ['espresso_node.py', 'espresso_node.py'], 
    args_list=[
        ['-l', box_l[0], '--salt'], 
        ['-l', box_l[1], '--gel', '-MPC', 15, '-bond_length', 0.966, '-alpha', 0.1]], 
    python_executable = 'python')
#%%
def populate_system(species_count):
    for i,side in enumerate(species_count):
        for species, count in side.items():
            print(f'Added {count} of {species}', end = ' ')
            print(*[f'{attr}={val}' for attr, val in PARTICLE_ATTR[species].items()], end = ' ')
            print(f'to side {i} ')
            server(f"/populate({count}, **{PARTICLE_ATTR[species]})", i)
populate_system(MOBILE_SPECIES_COUNT)
#%%
server('system.box_l',0).result()
#%%
def setup_non_bonded(non_bonded_attr):
    request_body = [
            f"system.non_bonded_inter{list(part_type)}.lennard_jones.set_params(**{kwargs})"
            for part_type, kwargs in non_bonded_attr.items() 
        ]
    server(request_body, SIDES)
setup_non_bonded(NON_BONDED_ATTR)
#%%
def setup_system():
    ##add LJ interactions and thermostats### 
    request_body = [
            "system.__setattr__('time_step', 0.001)",
            "system.cell_system.__setattr__('skin', 0.4)",
            "system.thermostat.set_langevin(kT=1, gamma=1, seed=42)",
            "system.minimize_energy.init(f_max=50, gamma=30.0, max_steps=10000, max_displacement=0.001)",
            "system.minimize_energy.minimize()"
        ]
    server(request_body, [0,1])

    ##switch on electrostatics
    if ELECTROSTATIC:
        server.request(
            f"system.actors.add(espressomd.electrostatics.P3M(prefactor={l_bjerrum * temp},accuracy=1e-3))",
            [0,1]
        )

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
mc.current_state['particles_info'].groupby(by = ['side', 'type']).size()
# %%
mc.step()
