#%%
import numpy as np
import json

import socket_nodes

from ion_pair_monte_carlo import MonteCarloPairs
from ion_pair_monte_carlo import auto_MC_collect

DIAMOND_PARTICLES = 248

PYTHON_EXECUTABLE = 'python'

import logging
logging.basicConfig(level=logging.DEBUG, stream=open('server.log', 'w'))


def populate_boxes(server, N1, N2, electrostatic):
    SIDES = [0,1]#for readability e.g. in list comprehensions
    MOBILE_SPECIES_COUNT = [
            {'anion' : int(N1/2), 'cation' : int(N1/2)}, #left side
            {'anion' : int(N2/2), 'cation' : int(N2/2)}, #right side
        ]
    def populate_system(species_count):
        from espresso_nodes.shared import PARTICLE_ATTR
        for i,side in enumerate(species_count):
            for species, count in side.items():
                print(f'Added {count} of {species}', end = ' ')
                print(*[f'{attr}={val}' for attr, val in PARTICLE_ATTR[species].items()], end = ' ')
                print(f'to side {i} ')
                server(f"populate({count}, **{PARTICLE_ATTR[species]})", i)
    populate_system(MOBILE_SPECIES_COUNT)
    ##switch on electrostatics
    if electrostatic:
        l_bjerrum = 2.0
        temp = 1
        server.request(
            f"system.actors.add(espressomd.electrostatics.P3M(prefactor={l_bjerrum * temp},accuracy=1e-3))",
            SIDES
        )
        #minimize energy and run md
        server([
            "system.minimize_energy.init(f_max=50, gamma=30.0, max_steps=10000, max_displacement=0.001)",
            "system.minimize_energy.minimize()",
            f"system.integrator.run({10000})"
            ],
            SIDES
        )

    server('system.minimize_energy.minimize()', [0,1])
    print('two box system with polyelectolyte (client 1) initialized')


def equilibration(MC, gel_md_steps : int, salt_md_steps : int, mc_steps : int, rounds : int = 10):
    from tqdm import trange
    for ROUND in trange(rounds):
        for MC_STEP in trange(mc_steps):
            MC.step()
        MC.server(f'integrate(int_steps = {salt_md_steps}, n_samples =1)',0)
        MC.server(f'integrate(int_steps = {gel_md_steps}, n_samples =1)',1)


def collect_data(MC, pressure_target_error=2, mc_target_error=0.001, rounds : int = 5, timeout = 180):
    n_mobile = []
    pressure_salt = []
    pressure_gel = []
    from tqdm import trange
    for ROUND in trange(rounds):
        n_mobile.append(auto_MC_collect(MC, mc_target_error, 100, timeout = timeout))
        request = MC.server(f'auto_integrate_pressure({pressure_target_error}, initial_sample_size = 1000, timeout = {timeout})', [0,1])
        pressure_salt.append(request[0].result())
        pressure_gel.append(request[1].result())
        print(MC.setup())
    keys = ['mean', 'err', 'eff_sample_size']
    return_dict =  {
        'n_mobile_salt': {k:v.tolist() for k,v in zip(keys,np.array(n_mobile).T)}, 
        'pressure_salt' : {k:v.tolist() for k,v in zip(keys,np.array(pressure_salt).T)}, 
        'pressure_gel' : {k:v.tolist() for k,v in zip(keys,np.array(pressure_gel).T)}}
    return return_dict

#%%
def main(electrostatic, system_volume, N_particles, v_gel, n_gel, alpha):
    #box volumes and dimmensions
    V = [system_volume*(1-v_gel),system_volume*v_gel]
    box_l = [V_**(1/3) for V_ in V]

    #real alpha and counterions amount
    charged_gel_particles = int(DIAMOND_PARTICLES*alpha)
    alpha = charged_gel_particles/DIAMOND_PARTICLES

    #mobile ions on both sides, 
    #note we have some counterions already in the gel
    N = [
        int(np.round(N_particles*n_gel)),
        int(np.round(N_particles*(1-n_gel)))
        ]

    ###start server and nodes
    import subprocess
    server = socket_nodes.utils.create_server_and_nodes(
        scripts = ['espresso_nodes/node.py']*2, 
        args_list=[
            ['-l', box_l[0], '--salt'],
            ['-l', box_l[1], '--gel', '-MPC', 15, '-bond_length', 0.966, '-alpha', alpha]
            ], 
        python_executable = PYTHON_EXECUTABLE, 
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE,
        )
    
    #populate_boxes(server, N[0], N[1] - charged_gel_particles, electrostatic)
    populate_boxes(server, N[0], N[1], electrostatic)
    MC = MonteCarloPairs(server)
    
    return server, MC
#%%
electrostatic = False
system_vol = 20**3*2
N=200
v_gel = 0.4
n_gel = v_gel
alpha = 0.25
server, MC = main(electrostatic, system_vol, N, v_gel, v_gel, alpha)

# %%
server("increment_volume(1000)", 1).result()