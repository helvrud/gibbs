#%%
import logging
import numpy as np
from pandas.core import series

import socket_nodes
from monte_carlo.ion_pair import MonteCarloPairs
#%%
logger  = logging.getLogger('Server')
logging.basicConfig(stream=open('server.log', 'w'), level=logging.WARNING)
#%%
###Control parameters
ELECTROSTATIC = False
system_volume = 20**3*2 #two boxes volume
v_gel = 0.5 #relative volume of the box with fixed anions
N1 = 100 #mobile ions on the left side
N2 = 100 #mobile ions on the right side
#box volumes and dimmensions
V = [system_volume*(1-v_gel),system_volume*v_gel]
box_l = [V_**(1/3) for V_ in V]

###start server and nodes
server = socket_nodes.utils.create_server_and_nodes(
    scripts = ['espresso_nodes/node.py']*2, 
    args_list=[
        ['-l', box_l[0], '--salt'],
        ['-l', box_l[1], '--gel', '-MPC', 15, '-bond_length', 0.966, '-alpha', 0.00]
        ], 
    python_executable = 'python')

#%%
def setup_two_box_system():
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
    if ELECTROSTATIC:
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
setup_two_box_system()
#%%    
MC = MonteCarloPairs(server)
# %%
def equilibration(gel_md_steps, salt_md_steps, mc_steps, rounds):
    from tqdm import trange
    for ROUND in trange(rounds):
        for MC_STEP in trange(mc_steps):
            MC.step()
        server(f'integrate(int_steps = {salt_md_steps}, n_samples =1)',0)
        server(f'integrate(int_steps = {gel_md_steps}, n_samples =1)',1)
#%%
tau_gel = 40
tau_salt = 7
eff_sample_size = 1000
md_steps = (N1+N2)*3
rounds=10
equilibration(eff_sample_size*tau_gel*2, eff_sample_size*tau_salt*2, md_steps, rounds)
# %%
def collect_data(gel_md_steps, salt_md_steps, mc_steps, rounds):
    n_mobile = []
    pressure_salt = []
    pressure_gel = []
    from tqdm import trange
    for ROUND in trange(rounds):
        for MC_STEP in trange(mc_steps):
            MC.step()
            n_mobile.append(MC.current_state['n_mobile'])
        server(f'integrate(int_steps = {salt_md_steps}, n_samples =1)',0)
        server(f'integrate(int_steps = {gel_md_steps}, n_samples =1)',1)