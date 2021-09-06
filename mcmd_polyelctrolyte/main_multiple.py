#%%
import numpy as np
import json

import socket_nodes
from monte_carlo.ion_pair import MonteCarloPairs
from monte_carlo.ion_pair import auto_MC_collect
#logger  = logging.getLogger('Server')
#logging.basicConfig(stream=open('server.log', 'w'), level=logging.WARNING)
def run(v_gel, ELECTROSTATIC):
    ###Control parameters

    system_volume = 20**3*2 #two boxes volume

    N1 = 100 #mobile ions on the left side
    N2 = 100 #mobile ions on the right side
    #box volumes and dimmensions
    V = [system_volume*(1-v_gel),system_volume*v_gel]
    box_l = [V_**(1/3) for V_ in V]
    alpha =0.05
    diamond_particles = 248

    charged_gel_particles = int(diamond_particles*alpha)
    alpha = charged_gel_particles/diamond_particles

    N2 = N2 - charged_gel_particles

    ###start server and nodes
    server = socket_nodes.utils.create_server_and_nodes(
        scripts = ['espresso_nodes/node.py']*2, 
        args_list=[
            ['-l', box_l[0], '--salt'],
            ['-l', box_l[1], '--gel', '-MPC', 15, '-bond_length', 0.966, '-alpha', 0.05]
            ], 
        python_executable = 'python')

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

    MC = MonteCarloPairs(server)

    def equilibration(gel_md_steps : int, salt_md_steps : int, mc_steps : int, rounds : int):
        from tqdm import trange
        for ROUND in trange(rounds):
            for MC_STEP in trange(mc_steps):
                MC.step()
            server(f'integrate(int_steps = {salt_md_steps}, n_samples =1)',0)
            server(f'integrate(int_steps = {gel_md_steps}, n_samples =1)',1)

    tau_gel = 4
    tau_salt = 4
    eff_sample_size = 1000
    mc_steps = (N1+N2)*3
    rounds=10
    equilibration(int(eff_sample_size*tau_gel*2), int(eff_sample_size*tau_salt*2), int(mc_steps), rounds)

    def collect_data(pressure_target_error, mc_target_error, rounds : int, timeout = 180):
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
            'alpha' : alpha,
            'v' : v_gel,
            'system_volume' : system_volume,
            'n_mobile' : N1+N2+charged_gel_particles,
            'n_mobile_salt': {k:v.tolist() for k,v in zip(keys,np.array(n_mobile).T)}, 
            'pressure_salt' : {k:v.tolist() for k,v in zip(keys,np.array(pressure_salt).T)}, 
            'pressure_gel' : {k:v.tolist() for k,v in zip(keys,np.array(pressure_gel).T)}}
        return return_dict

    collected_data = collect_data(pressure_target_error=0.001, mc_target_error=2, rounds=5)
    savefname= f'../data/alpha_{alpha}_v_{v_gel}_N_{N1+N2}_volume_{system_volume}_electrostatic_{ELECTROSTATIC}.json'
    with open(savefname, 'w') as outfile:
        json.dump(collected_data, outfile)

    print (collected_data)

if __name__=='__main__':
    import argparse
    import sys
    parser = argparse.ArgumentParser(description='IP')
    parser.add_argument('v_gel',
                        metavar='v_gel',
                        type=float,
                        help='v_gel')
    parser.add_argument('ELECTROSTATIC',
                        metavar='ELECTROSTATIC',
                        type=bool,
                        help='ELECTROSTATIC')
    
    args = parser.parse_args()
    run(args.v_gel, args.ELECTROSTATIC)