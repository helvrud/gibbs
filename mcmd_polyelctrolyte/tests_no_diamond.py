#%%
import numpy as np
import json
import uuid

import socket_nodes
from tqdm import trange

from ion_pair_monte_carlo import MonteCarloPairs

PYTHON_EXECUTABLE = 'python'

import logging
logging.basicConfig(level=logging.DEBUG, stream=open('server.log', 'w'))

def mol_to_n(mol_conc, unit_length_nm=0.35):
    #Navogadro = 6.02214e23
    #1e-9**3 * 10**3 = 10e-24
    #6.022e23*10e-24 = 6.022e-1 
    n = unit_length_nm**3*6.02214e-1*mol_conc
    return n


def build_MC(
    Volume, N_pairs, A_fixed, 
    log_names, electrostatic=False, 
    no_interaction=False, 
    python_executable = 'python'):
    
    #box volumes and dimmensions
    box_l = [V_**(1/3) for V_ in Volume]

    ###start server and nodes
    import subprocess
    server = socket_nodes.utils.create_server_and_nodes(
        scripts = ['espresso_nodes/run_node.py']*2, 
        args_list=[
            ['-l', box_l[0], '--salt', '-no_interaction', no_interaction, "-log_name", log_names[0]],
            ['-l', box_l[1], '--salt', '-no_interaction', no_interaction, "-log_name", log_names[1]],
            ], 
        python_executable = python_executable, 
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE,
        )
    ###simulate polyelectrolyte without diamond structure
    from espresso_nodes.shared import PARTICLE_ATTR
    ##add counterions
    server(f"populate({A_fixed}, **{PARTICLE_ATTR['cation']})", 1)
    ##add fixed anions
    server(f"populate({A_fixed}, **{PARTICLE_ATTR['gel_anion']})", 1)

    MC = MonteCarloPairs(server)
    
    MC.populate(N_pairs)

    if electrostatic: 
        server('enable_electrostatic()', [0,1])
        print("Electrostatic is enabled")
    
    return MC

#%%
MC = build_MC([20000,20000], [100,100], 50, ['box_0.log', 'box_1.log'])
#MC.equilibrate()
# %%
server = MC.server
# %%
server("system.part.select(q=0)", 0).result()
# %%
