#%%
from socket_nodes import Server
import socket_nodes
from monte_carlo import MonteCarloPairs, current_state_to_record

import random
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm
import sys

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(stream=open('server_log', 'w'), level=logging.DEBUG)


from shared_data import V_all, PARTICLE_ATTR, MOBILE_SPECIES_COUNT

#box volumes and dimmensions
v = 0.5 #relative volume of the gel box
V = [V_all*(1-v),V_all*v]
box_l = [V_**(1/3) for V_ in V]

###start server and nodes
server = socket_nodes.utils.create_server_and_nodes(
    scripts = ['espresso_node.py', 'espresso_node.py'], 
    args_list=[
        ['-l', box_l[0], '--salt'],
        ['-l', box_l[1], '--gel', '-MPC', 15, '-bond_length', 0.966, '-alpha', 0.00]], 
    python_executable = 'python', stdout = open('log', 'w'))

def populate_system(species_count):
    for i,side in enumerate(species_count):
        for species, count in side.items():
            print(f'Added {count} of {species}', end = ' ')
            print(*[f'{attr}={val}' for attr, val in PARTICLE_ATTR[species].items()], end = ' ')
            print(f'to side {i} ')
            server(f"populate({count}, **{PARTICLE_ATTR[species]})", i)
populate_system(MOBILE_SPECIES_COUNT)

##switch on electrostatics
from shared_data import ELECTROSTATIC, l_bjerrum, temp
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
server('system.minimize_energy.minimize()', [0,1])
MC = MonteCarloPairs(server)
# %%
mc_df = pd.DataFrame()
md_df = pd.DataFrame()
step = 0
#%%
for k in range(10):
    for i in range(1000):
        mc_df = mc_df.append(
            current_state_to_record(
                MC.step(), step
            ), 
            ignore_index=True
        )
        mc_df['note'] = 'equilibration'
        step+=1
    r = server('run_md(200000,20000)',[0,1])
    P_Re = pd.DataFrame(r[1].result()).add_prefix('Re_')
    P_Re['Pressure'] = r[0].result()
    md_df=md_df.append(P_Re, ignore_index=True)
    MC.current_state=MC.setup()
    print(k,i)
# %%
mc_df.to_csv('mc_20_alpha_0.csv')
md_df.to_csv('md_20_alpha_0.csv')