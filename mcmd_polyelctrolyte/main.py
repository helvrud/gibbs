import numpy as np
import json

import socket_nodes

from monte_carlo.ion_pair import MonteCarloPairs
from monte_carlo.ion_pair import auto_MC_collect

#change cwd to file location
import os
import sys
os.chdir(os.path.dirname(sys.argv[0]))

#particles between the nodes
MPC = 15
#all gel particles
DIAMOND_PARTICLES = MPC*16+8

#path to python executable, can be pypresso
PYTHON_EXECUTABLE = 'python'

#set True to check pure Donnan
NO_INTERACTION = True

def populate_boxes(server, N0_pairs, N1_pairs):
    #import particles attributes consistent with other parts of the program
    from espresso_nodes.shared import PARTICLE_ATTR
    MOBILE_SPECIES_COUNT = [
            {'anion' : int(N0_pairs), 'cation' : int(N0_pairs)}, #left side
            {'anion' : int(N1_pairs), 'cation' : int(N1_pairs)}, #right side
        ]
    for i,side in enumerate(MOBILE_SPECIES_COUNT):
        for species, count in side.items():
            print(f'Added {count} of {species}', end = ' ')
            print(*[f'{attr}={val}' for attr, val in PARTICLE_ATTR[species].items()], end = ' ')
            print(f'to side {i} ')
            server(f"populate({count}, **{PARTICLE_ATTR[species]})", i)
    server('system.minimize_energy.minimize()', [0,1])
    print('two box system with polyelectrolite (client 1) is initialized')
    
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
        "system.minimize_energy.init(f_max=50, gamma=30.0, max_steps=10000, max_displacement=0.001)",
        "system.minimize_energy.minimize()",
        f"system.integrator.run({10000})"
        ],
        SIDES
    )
    server('system.minimize_energy.minimize()', [0,1])
    print("Electrostatic is enabled")

def equilibration(MC, gel_md_steps : int, salt_md_steps : int, mc_steps : int, rounds : int = 10):
    MC.server(f'integrate(int_steps = {salt_md_steps}, n_samples =1)',0)
    MC.server(f'integrate(int_steps = {gel_md_steps}, n_samples =1)',1)
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
    MC.setup()
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

def main(electrostatic, system_volume, N_pairs, v_gel, n_gel, alpha):
    # box volumes and dimmensions
    V = [system_volume*(1-v_gel),system_volume*v_gel]
    box_l = [V_**(1/3) for V_ in V]

    # real alpha and counterions amount
    charged_gel_particles = int(DIAMOND_PARTICLES*alpha)
    alpha = charged_gel_particles/DIAMOND_PARTICLES

    # mobile ions on both sides, 
    # note we have some counterions already in the gel, 
    # that is not accounted here
    N = [
        int(np.round(N_pairs*(1-n_gel))),
        int(np.round(N_pairs*n_gel))
        ]

    ###start server and nodes
    server = socket_nodes.utils.create_server_and_nodes(
        #paths to entry point scripts
        scripts = ['espresso_nodes/node.py']*2,
        args_list=[
            ['-l', box_l[0], '--salt', '-no_interaction', NO_INTERACTION],
            ['-l', box_l[1], '--gel', '-MPC', 15, '-bond_length', 0.966, '-alpha', alpha, '-no_interaction', NO_INTERACTION]
            ], 
        python_executable = PYTHON_EXECUTABLE, 
        stdout = open('server.log', 'w'),
        stderr = open('server.log', 'w'),
        )
    
    populate_boxes(server, N[0], N[1])
    if electrostatic: enable_electrostatic(server)
    MC = MonteCarloPairs(server)
    
    ###This values are from the experience of previous runs
    #autocorrelation times, will be rewritten to calculate anew
    tau_gel = 4
    tau_salt = 4
    #at least this amount of independent steps needed for MD
    eff_sample_size = 1000
    #minimal steps of MD required
    md_gel = int(eff_sample_size*tau_gel*2)
    md_salt =int(eff_sample_size*tau_salt*2)
    #minimal steps of MC
    mc_steps = sum(N)*5

    equilibration(MC, md_gel, md_salt, int(mc_steps))
    
    collected_data = collect_data(MC)
    collected_data.update({
            'alpha' : alpha, #charged gel monomers fraction
            'v' : v_gel, #relative gel volume
            'system_volume' : system_volume, #system volume
            'n_pairs' : N_pairs, #Number of added ion pairs, excl. counterions
            'electrostatic' : electrostatic, #is electrostatic enabled
            'n_gel' : DIAMOND_PARTICLES, #number of all gel particles
            'anion_fixed' : charged_gel_particles, #number of charged gel particles
            'box_l' : box_l, #box_lengths
            'volume' : V, #volumes
            'no_interaction' : NO_INTERACTION, #no interaction flag, True if no LJ and FENE
        })
    str_alpha = "{:.3f}".format(alpha)
    import uuid
    
    save_fname = f'../data/{str_alpha}_{v_gel}_{N_pairs}_{system_volume}_{int(electrostatic)}_{int(NO_INTERACTION)}_'+str(uuid.uuid4())[:8]+'.json'
    with open(save_fname, 'w') as outfile:
        json.dump(collected_data, outfile)

    return collected_data

if __name__=="__main__":
    from functools import partial
    from multiprocessing import Pool
    electrostatic = False
    system_vol = 25**3*2
    N_pairs=100
    v_gel = [0.4, 0.45, 0.5, 0.55, 0.6]
    alpha = 0
    def worker(v_gel):
        n_gel = v_gel
        return main(electrostatic=electrostatic, system_volume=system_vol, N_pairs=N_pairs, n_gel = n_gel, alpha=alpha, v_gel = v_gel)
    with Pool(5) as p:
        r = p.map(worker, v_gel)
    print(r)
