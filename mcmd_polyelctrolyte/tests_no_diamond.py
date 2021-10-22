#%%
import numpy as np
import json

import socket_nodes

from ion_pair_monte_carlo import MonteCarloPairs, zeta_on_system_state

PYTHON_EXECUTABLE = 'python'

import logging
logging.basicConfig(level=logging.DEBUG, stream=open('server.log', 'w'))


def populate_boxes(server, N_pairs_salt, N_pairs_gel):
    MOBILE_SPECIES_COUNT = [
            {'anion' : int(N_pairs_salt), 'cation' : int(N_pairs_salt)}, #left side
            {'anion' : int(N_pairs_gel), 'cation' : int(N_pairs_gel)}, #right side
        ]
    from espresso_nodes.shared import PARTICLE_ATTR
    for i,side in enumerate(MOBILE_SPECIES_COUNT):
        for species, count in side.items():
            print(f'Added {count} of {species}', end = ' ')
            print(*[f'{attr}={val}' for attr, val in PARTICLE_ATTR[species].items()], end = ' ')
            print(f'to side {i} ')
            server(f"populate({count}, **{PARTICLE_ATTR[species]})", i)
    
    print('two box system initialized')

#%%
def build_MC(system_volume, N_pairs_all, v_gel, n_gel, alpha, gel_particles):
    #box volumes and dimmensions
    V = [system_volume*(1-v_gel),system_volume*v_gel]
    box_l = [V_**(1/3) for V_ in V]

    #real alpha and counterions amount
    charged_gel_particles = int(gel_particles*alpha)
    alpha = charged_gel_particles/gel_particles

    #mobile ions on both sides, 
    #note we have some counterions already in the gel
    N_pairs = [
        int(np.round(N_pairs_all*n_gel)),
        int(np.round(N_pairs_all*(1-n_gel)))
        ]

    ###start server and nodes
    import subprocess
    server = socket_nodes.utils.create_server_and_nodes(
        scripts = ['espresso_nodes/run_node.py']*2, 
        args_list=[
            ['-l', box_l[0], '--salt'],
            ['-l', box_l[1], '--salt'],
            #['-l', box_l[1], '--gel', '-MPC', 15, '-bond_length', 0.966, '-alpha', alpha]
            ], 
        python_executable = PYTHON_EXECUTABLE, 
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE,
        )
    
    populate_boxes(server, *N_pairs)
    
    ###simulate polyelectrolyte without diamond structure
    from espresso_nodes.shared import PARTICLE_ATTR
    server(f"populate({charged_gel_particles}, **{PARTICLE_ATTR['cation']})", 1)
    server(f"populate({charged_gel_particles}, **{PARTICLE_ATTR['gel_anion']})", 1)
    MC = MonteCarloPairs(server)
    
    return MC


def equilibrate_MC(MC):
    md_steps = 10000
    mc_steps = 200
    MC.server(f'integrate(int_steps = {md_steps}, n_samples =1)',0)
    MC.server(f'integrate(int_steps = {md_steps}, n_samples =1)',1)
    rounds = 5
    from tqdm import trange
    for ROUND in trange(rounds):
        MC.setup()
        [MC.step() for i in range(mc_steps)]
        MC.server(f'integrate(int_steps = {md_steps}, n_samples =1)',0)
        MC.server(f'integrate(int_steps = {md_steps}, n_samples =1)',1)
    MC.setup()
    return True
#%%
system_vol = 10**3*2
N_pairs=100
v_gel = [0.4, 0.5, 0.6]
alpha = 25/248
gel_particles = 248
# %%
def zeta_from_analytic(N_pairs, fixed_anions, v):
    import numpy as np
    if v == 0.5: v=0.49999999 #dirty
    sqrt = np.sqrt
    return v*(N_pairs - (fixed_anions*(1 - v)**2/2 + N_pairs*v**2 - (1 - v)*sqrt(fixed_anions**2*(1 - v)**2 + 4*fixed_anions*N_pairs*v**2 + 4*N_pairs**2*v**2)/2)/(v**2 - (1 - v)**2))/((1 - v)*(fixed_anions + (fixed_anions*(1 - v)**2/2 + N_pairs*v**2 - (1 - v)*sqrt(fixed_anions**2*(1 - v)**2 + 4*fixed_anions*N_pairs*v**2 + 4*N_pairs**2*v**2)/2)/(v**2 - (1 - v)**2)))
# %%
v_gel = 0.4
MC = build_MC(system_volume=system_vol, N_pairs_all=N_pairs, n_gel = v_gel, alpha=alpha, v_gel = v_gel, gel_particles=gel_particles)
#%%
equilibrate_MC(MC)
# %%
MC.sample_zeta_to_target_error(timeout = 30)
# %%
zeta_from_analytic(N_pairs, gel_particles*alpha, v_gel)
#%%
def worker(v_gel):
    n_gel = v_gel
    MC = build_MC(system_volume=system_vol, N_pairs_all=N_pairs, n_gel = n_gel, alpha=alpha, v_gel = v_gel, gel_particles=gel_particles)
    equilibrate_MC(MC)
    zeta, zeta_err, sample_size = MC.sample_zeta_to_target_error()
    return zeta
#%%
from multiprocessing import Pool
with Pool(5) as p:
    zeta = p.map(worker, v_gel)
print(zeta)
#%%
import matplotlib.pyplot as plt
zeta_an = [zeta_from_analytic(N_pairs, gel_particles*alpha, v_) for v_ in v_gel]
plt.scatter(v_gel, zeta, marker = 's')
plt.plot(v_gel, zeta_an)