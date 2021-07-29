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
import sys

PAIR = [0,1]#for readability in list comprehensions
SIDES = [0,1]#for readability in list comprehensions

###start server and nodes
server = socket_nodes.utils.create_server_and_nodes(
    scripts = ['espresso_node.py', 'espresso_node.py'], 
    args_list=[
        ['-l', box_l[0], '--salt'],
        ['-l', box_l[1], '--salt'],],
        #['-l', box_l[1], '--gel', '-MPC', 15, '-bond_length', 0.966, '-alpha', 0.1]], 
    python_executable = 'python', stdout = open('log', 'w'))
#%%
def populate_system(species_count):
    for i,side in enumerate(species_count):
        for species, count in side.items():
            print(f'Added {count} of {species}', end = ' ')
            print(*[f'{attr}={val}' for attr, val in PARTICLE_ATTR[species].items()], end = ' ')
            print(f'to side {i} ')
            server(f"populate({count}, **{PARTICLE_ATTR[species]})", i)
populate_system(MOBILE_SPECIES_COUNT)
#%%
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
#%%
MC = MonteCarloSocketNodes(server)
# %%
result=pd.DataFrame()
#%%
for round in tqdm.tqdm_notebook(range(10)):
    energy = []
    for i in tqdm.tqdm_notebook(range(100)):
        energy.append(MC.step()['energy'])
    energy_mc= np.array(energy).T
    md_request = server('run_md(100000, 1000)',[0,1])
    energy_md = np.array([r.result() for r in md_request])
    mc = np.vstack((energy_mc, np.array(['mc']*energy_mc.shape[1])))
    md = np.vstack((energy_md, np.array(['md']*energy_md.shape[1])))
    mc_md = np.hstack((mc,md))
    
    df= pd.DataFrame(mc_md.T, columns=['left', 'right', 'simulation'])
    df['step'] = list(range(len(df)))
    df['round'] = round
    step = len(df)
    df = df.melt(
        value_vars=['left', 'right'],
        id_vars=['round','step','simulation']
        ).rename(
            columns = {'variable':'side', 'value':'energy'}
        ).astype({'energy' : float})
    result = result.append(df, ignore_index=True)
for idx, group in result.groupby(by = 'round'):
    indices = group.index
    result.loc[indices, 'x'] = np.arange(len(group))+idx*400
#%%
import seaborn as sns
g = sns.relplot(
    data = result, 
    x = 'x',
    y = 'energy', 
    hue = 'simulation',
    col = 'side',
    facet_kws={'sharey': False, 'sharex': True},
    kind = 'line'
    )


# %%
particles = server("part_data((None,None), {'type':'int','q':'int', 'pos':'list'})", 1).result()
df = pd.DataFrame(particles)
df.q = df.q.astype('category')
df[['x', 'y', 'z']] = df.pos.apply(pd.Series)
import plotly.express as px
fig = px.scatter_3d(df, x='x', y='y', z='z', color ='q', symbol = 'type')
fig.show('browser')
#%%
MC.current_state
