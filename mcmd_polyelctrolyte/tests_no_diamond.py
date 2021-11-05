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

def build_MC(system_volume, N_pairs_all, v_gel, n_gel, alpha, gel_particles, log_names, electrostatic=False,  no_interaction=False):
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
            ['-l', box_l[0], '--salt', '-no_interaction', no_interaction, "-log_name", log_names[0]],
            ['-l', box_l[1], '--salt', '-no_interaction', no_interaction, "-log_name", log_names[1]],
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

    if electrostatic: 
        server('enable_electrostatic()', [0,1])
        print("Electrostatic is enabled")
    MC = MonteCarloPairs(server)
    
    return MC

def zeta_from_analytic(N_pairs, fixed_anions, v):
    import numpy as np
    if v == 0.5: v=0.49999999 #dirty
    sqrt = np.sqrt
    return v*(N_pairs - (fixed_anions*(1 - v)**2/2 + N_pairs*v**2 - (1 - v)*sqrt(fixed_anions**2*(1 - v)**2 + 4*fixed_anions*N_pairs*v**2 + 4*N_pairs**2*v**2)/2)/(v**2 - (1 - v)**2))/((1 - v)*(fixed_anions + (fixed_anions*(1 - v)**2/2 + N_pairs*v**2 - (1 - v)*sqrt(fixed_anions**2*(1 - v)**2 + 4*fixed_anions*N_pairs*v**2 + 4*N_pairs**2*v**2)/2)/(v**2 - (1 - v)**2)))

def save_results(save_data, v_gel):
    import os
    script_name = os.path.basename(__file__).split('.')[0]
    save_fname = '../data/'+script_name+f'/{alpha}_{v_gel}_{N_pairs}_{system_vol}_{int(electrostatic)}_{int(no_interaction)}_'+str(uuid.uuid4())[:8]+'.json'
    from pathlib import Path
    Path('../data/'+script_name).mkdir(parents=True, exist_ok=True)
    with open(save_fname, 'w') as outfile:
        json.dump(save_data, outfile, indent=4)

#%%
#make sure we have enough particles ans system volume
min_conc = 0.01
min_N_pairs = 100
system_vol = min_N_pairs*2/mol_to_n(min_conc)

## INPUT ARGS
conc = 0.01 #mol/L
v_gel = [0.3, 0.4, 0.5, 0.6, 0.7]
v_gel = [0.4]
alpha = 124/248
no_interaction = False
electrostatic = False
cpu_count = 5

N_pairs=int(round(system_vol*mol_to_n(conc)/2))
gel_particles = 248
#%%
def worker(v):
    n_gel = v
    sample_size=10
    MC = build_MC(
        system_volume=system_vol, 
        N_pairs_all=N_pairs, 
        n_gel = n_gel, 
        alpha=alpha, 
        v_gel = v, 
        gel_particles=gel_particles,
        log_names=[f'salt_{round(v, 3)}_0.log', f'salt_{round(v, 3)}_1.log'],
        no_interaction=no_interaction,
        electrostatic=electrostatic)
    MC.equilibrate()
    zetas = []
    md_steps = 10000
    for i in trange(sample_size):
        zeta, *_ = MC.sample_zeta_to_target_error()
        #in between mc
        MC.run_md(md_steps)
        print(zeta)
        zetas.append(zeta)
    zeta_donnan = zeta_from_analytic(N_pairs, gel_particles*alpha, v)
    save_data = {
            'alpha' : alpha, #charged gel monomers fraction
            'v' : v, #relative gel volume
            'system_volume' : system_vol, #system volume
            'n_pairs' : N_pairs, #Number of added ion pairs, excl. counterions
            'electrostatic' : electrostatic, #is electrostatic enabled
            'n_gel' : gel_particles, #number of all gel particles
            'anion_fixed' : int(alpha*gel_particles), #number of charged gel particles
            'no_interaction' : no_interaction, #no interaction flag, True if no LJ and FENE
            'zeta' : zetas,
            #'zeta_err' : zeta_err,
            'zeta_donnan' : zeta_donnan,
        }
    save_results(save_data, v)
    return zeta
#%%
if __name__ == "__main__":
    from multiprocessing import Pool
    with Pool(cpu_count) as p:
        zeta = p.map(worker, v_gel)
    print(zeta)
# %%
