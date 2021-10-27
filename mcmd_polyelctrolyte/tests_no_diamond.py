#%%
import numpy as np
import json
import uuid

import socket_nodes
from tqdm.std import trange

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

def enable_electrostatic(server):
    SIDES = [0,1]#for readability e.g. in list comprehensions
    l_bjerrum = 2.0
    temp = 1
    server.request(
        f"system.actors.add(espressomd.electrostatics.P3M(prefactor={l_bjerrum * temp},accuracy=1e-3))",
        SIDES
    )
    #minimize energy and run md
    server([
        "system.minimize_energy.init(f_max=50, gamma=30.0, max_steps=10000, max_displacement=0.01)",
        "system.minimize_energy.minimize()",
        f"system.integrator.run({10000})"
        ],
        SIDES
    )
    server('system.minimize_energy.minimize()', [0,1])
    print("Electrostatic is enabled")

def build_MC(system_volume, N_pairs_all, v_gel, n_gel, alpha, gel_particles, log_names):
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
            ['-l', box_l[0], '--salt', '-no_interaction', NO_INTERACTION, "-log_name", log_names[0]],
            ['-l', box_l[1], '--salt', '-no_interaction', NO_INTERACTION, "-log_name", log_names[1]],
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

    if ELECTROSTATIC: enable_electrostatic(server)
    MC = MonteCarloPairs(server)
    
    return MC

def equilibrate_MC(MC, md_steps = 100000, mc_steps = 200):
    MC.server(f'system.integrator.run({md_steps})',[0,1])
    rounds = 25
    from tqdm import trange
    for ROUND in trange(rounds):
        MC.setup()
        [MC.step() for i in range(mc_steps)]
        MC.server(f'system.integrator.run({md_steps})',[0,1])
    MC.setup()
    return True

def zeta_from_analytic(N_pairs, fixed_anions, v):
    import numpy as np
    if v == 0.5: v=0.49999999 #dirty
    sqrt = np.sqrt
    return v*(N_pairs - (fixed_anions*(1 - v)**2/2 + N_pairs*v**2 - (1 - v)*sqrt(fixed_anions**2*(1 - v)**2 + 4*fixed_anions*N_pairs*v**2 + 4*N_pairs**2*v**2)/2)/(v**2 - (1 - v)**2))/((1 - v)*(fixed_anions + (fixed_anions*(1 - v)**2/2 + N_pairs*v**2 - (1 - v)*sqrt(fixed_anions**2*(1 - v)**2 + 4*fixed_anions*N_pairs*v**2 + 4*N_pairs**2*v**2)/2)/(v**2 - (1 - v)**2)))

def save_results(save_data, v_gel):
    import os
    script_name = os.path.basename(__file__).split('.')[0]
    save_fname = '../data/'+script_name+f'/{alpha}_{v_gel}_{N_pairs}_{system_vol}_{int(ELECTROSTATIC)}_{int(NO_INTERACTION)}_'+str(uuid.uuid4())[:8]+'.json'
    from pathlib import Path
    Path('../data/'+script_name).mkdir(parents=True, exist_ok=True)
    with open(save_fname, 'w') as outfile:
        json.dump(save_data, outfile, indent=4)

#%%
N_pairs=100
conc = 0.1 #mol/L
system_vol = N_pairs*2/mol_to_n(conc)
v_gel = [0.3, 0.4, 0.5, 0.6, 0.7]
alpha = 25/248
gel_particles = 248
NO_INTERACTION = False
ELECTROSTATIC = False
#%%
#one call test
#v_gel_once = 0.5
#MC = build_MC(system_volume=system_vol, N_pairs_all=N_pairs, n_gel = v_gel_once, alpha=alpha, v_gel = v_gel_once, gel_particles=gel_particles)
#equilibrate_MC(MC)
#zeta, zeta_err, sample_size = MC.sample_zeta_to_target_error()
#zeta_an = zeta_from_analytic(N_pairs, gel_particles*alpha, v_gel_once)
#print(zeta, zeta_an)
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
        log_names=[f'salt_{round(v, 3)}_0.log', f'salt_{round(v, 3)}_1.log'])
    equilibrate_MC(MC)
    zetas = []
    md_steps = 10000
    for i in trange(sample_size):
        zeta, *_ = MC.sample_zeta_to_target_error()
        #in between mc
        MC.server(f'system.integrator.run({md_steps})',[0,1])
        MC.setup()
        print(zeta)
        zetas.append(zeta)
    zeta_donnan = zeta_from_analytic(N_pairs, gel_particles*alpha, v)
    save_data = {
            'alpha' : alpha, #charged gel monomers fraction
            'v' : v, #relative gel volume
            'system_volume' : system_vol, #system volume
            'n_pairs' : N_pairs, #Number of added ion pairs, excl. counterions
            'electrostatic' : ELECTROSTATIC, #is electrostatic enabled
            'n_gel' : gel_particles, #number of all gel particles
            'anion_fixed' : int(alpha*gel_particles), #number of charged gel particles
            'no_interaction' : NO_INTERACTION, #no interaction flag, True if no LJ and FENE
            'zeta' : zetas,
             #'zeta_err' : zeta_err,
            'zeta_donnan' : zeta_donnan,
        }
    save_results(save_data, v)
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
# %%
