"""
The script here is used to espressomd.System with a cross-linked polymer chain (gel).
The gel has some of the monomers ionized, ionized monomers position are random.
The number of ionized monomers is defined by alpha = N_ion/N_all.
During the generation process counter-ions for the ionized monomers will be created.
"""
#%%
import sys
import espressomd
from montecarlo.libmontecarlo import sample_to_target_error
import numpy as np
import random
import logging
logging.getLogger("init_diamond_system.py")

def init_diamond_system(MPC, bond_length, alpha, bonded_attr, non_bonded_attr, particle_attr, target_l=None, target_pressure=None):
    import espressomd.interactions
    import espressomd.polymer
    a = (MPC + 1) * bond_length / (0.25 * np.sqrt(3))
    box_l = [a]*3
    system = espressomd.System(box_l = box_l)
    system.time_step = 0.001
    system.cell_system.skin = 0.4
    system.thermostat.set_langevin(kT=1, gamma=1, seed=42)
    #system.minimize_energy.init(f_max=50, gamma=60.0, max_steps=10000, max_displacement=0.001)

    logging.debug(f"gel initial volume: {box_l}")

    if non_bonded_attr is not None:
        setup_non_bonded(system, non_bonded_attr)
        logging.debug(f"non-bonded interaction is setup")

    if bonded_attr is not None:
        if non_bonded_attr is None:
            logging.debug(
                f"non-bonded interaction is not setup, bonded ignored")
        else:
            fene = espressomd.interactions.FeneBond(**bonded_attr['FeneBond'])
            system.bonded_inter.add(fene)
            logging.debug(f"bonded interaction is setup")

    start_id = system.part.highest_particle_id
    if bonded_attr is not None:
        #diamond.Diamond(a=a, bond_length=bond_length, MPC=MPC)
        espressomd.polymer.setup_diamond_polymer(system=system, bond=fene, MPC=MPC)
    else:
        for i in range(MPC*16+8):
            logging.debug(
                f"bonded interaction is not setup, no net created")
            system.part.add(pos = system.box_l*np.random.random(3), **particle_attr['gel_neutral'])
    gel_indices  = (start_id+1, system.part.highest_particle_id+1)

    re_type_nodes(system, gel_indices, particle_attr)
    charge_gel(system, gel_indices, alpha, particle_attr)
    minimize_energy(system, timeout=20)
    #logging.debug('Minimizing energy before volume change')
    #system.minimize_energy.minimize()
    if (target_pressure is not None) and (target_l is not None):
        raise ArithmeticError("Can not pass both target_pressure and target_l")
    if target_l is not None:
        change_volume(system, target_l)

    return system

def setup_non_bonded(system, non_bonded_attr):
    [system.non_bonded_inter[particle_types].lennard_jones.set_params(**lj_kwargs)
            for particle_types, lj_kwargs in non_bonded_attr.items()]


def re_type_nodes(system, gel_indices, particle_attr):
    """
    espresso/src/core/diamond.cpp
    int const type_bond = 0; first 8 nodes
    int const type_node = 0;
    int const type_cM = 1;
    int const type_nM = 1;
    int const type_CI = 2;
    """
    #
    N_NODES = 8

    particles = list(system.part[slice(*gel_indices)])
    for i, part in enumerate(particles):
        if i<8:
            for attr_name, attr_val in particle_attr['gel_node_neutral'].items():
                setattr(part, attr_name, attr_val)
        else:
            for attr_name, attr_val in particle_attr['gel_neutral'].items():
                setattr(part, attr_name, attr_val)

def charge_gel(system, gel_indices, alpha, particle_attr, add_counterions = True):
    particles = list(system.part[slice(*gel_indices)])
    n_charged = int(len(particles)*alpha)
    for i, part in enumerate(random.sample(particles, n_charged)):
        if part.type == particle_attr['gel_neutral']['type']:
            for attr_name, attr_val in particle_attr['gel_anion'].items():
                setattr(part, attr_name, attr_val)
        else: #part.type == particle_attr['gel_']:
            for attr_name, attr_val in particle_attr['gel_node_anion'].items():
                setattr(part, attr_name, attr_val)
        if add_counterions:
            system.part.add(pos = system.box_l*np.random.random(3), **particle_attr['cation'])
        logging.debug(f'{i+1}/{n_charged} charged')

def change_volume(system, target_l, scale_down_factor = 0.97, scale_up_factor = 1.05, int_steps = 10000):
    logging.debug (f'change_volume to the size L = {target_l}')
    while system.box_l[0] != target_l:
        factor = target_l/system.box_l[0]
        if factor<scale_down_factor:
            factor = scale_down_factor
        elif factor>scale_up_factor:
            factor = scale_up_factor
        d_new = system.box_l[0]*factor
        system.change_volume_and_rescale_particles(d_new)
        system.integrator.run(int_steps)
        logging.debug(f'gel box_size: {system.box_l[0]}')
        logging.debug(f"pressure: {system.analysis.pressure()['total']}")
    logging.debug ('volume change done')

def get_pressure(system, **kwargs):
    from montecarlo import sample_to_target_error
    def get_data_callback(n):
            acc = []
            for i in range(n):
                system.integrator.run(1000)
                acc.append(float(system.analysis.pressure()['total']))
            return acc
    return sample_to_target_error(get_data_callback, **kwargs)


def get_VP(system, V_min, V_max, V_step, direction = 'any', **sampling_kwargs):
    current_volume = system.box_l[0]**3
    l_min = V_min**(1/3)
    l_max = V_max**(1/3)
    V = np.arange(V_min, V_max+V_step, V_step)
    L = V**(1/3)
    if direction == 'any':
        if abs(V_min - current_volume) <= abs(V_max-current_volume):
            change_volume(system, l_min)
        else:
            change_volume(system, l_max)
            V = V[::-1]
    elif direction == 'compress':
        change_volume(system, l_max)
        V=V[::-1]
    elif direction == 'expand':
        change_volume(system, l_min)
    else:
        raise AttributeError("Invalid direction")

    P=[]
    P_err = []
    print(V)
    for v,l in zip(V,L):
        change_volume(system, target_l=l)
        pressure, pressure_err, eff_sample = get_pressure(system, **sampling_kwargs)
        P.append(pressure)
        P_err.append(pressure_err)
        print(f"V:{v}, l:{l}, P:{pressure}")
    return V, P, P_err


def _get_pairs(system, gel_start_id):
    pairs = [  (0, 1), (1, 2), (1, 3), (1, 4),
                (2, 5), (3, 6), (4, 7), (5, 0),
                (5, 3), (5, 4), (6, 0), (6, 4),
                (7, 0), (7, 2), (7, 3),]
    N_NODES = 8
    nodes = list(system.part[gel_start_id : gel_start_id+N_NODES])
    return [(nodes[pair[0]],nodes[pair[1]]) for pair in pairs]

def calc_Re(system, pairs):
    D = np.array([])
    for pair in pairs:
        box_l = system.box_l
        pos0 = pair[0].pos % box_l
        pos1 = pair[1].pos % box_l
        # this checks if the distance vector coordinates are bigger than the half of box_l
        # and if yes substitute  box_l from the coordinate
        Dvec =  abs(pos0 -pos1) - (abs((pos0 -pos1)) >  box_l/2 )*box_l
        Re = np.linalg.norm(Dvec)
        D = np.append(D, Re)
    return D

def  minimize_energy(system, timeout=60):
    import time
    system.thermostat.suspend()
    # minimize energy using min_dist as the convergence criterion
    system.integrator.set_steepest_descent(f_max=0, gamma=1e-3,
                                        max_displacement=0.01)
    start_time = time.time()
    while system.analysis.min_dist() < 0.5: #?
        elapsed_time = time.time() - start_time
        #print(f"minimization: {system.analysis.energy()['total']:+.2e}")
        #print(f"min_dist: {system.analysis.min_dist():+.2e}")
        system.integrator.run(20)
        if elapsed_time>timeout:
            print(timeout)
            break

    #print(f"minimization: {system.analysis.energy()['total']:+.2e}")
    print()
    system.integrator.set_vv()

    # activate thermostat
    system.thermostat.set_langevin(kT=1.0, gamma=1.0)
#%%
if __name__=='__main__':
    from shared import PARTICLE_ATTR, BONDED_ATTR, NON_BONDED_ATTR
    #BONDED_ATTR = None
    #NON_BONDED_ATTR = None
    #system = init_diamond_system(15,0.966,0.5, BONDED_ATTR, NON_BONDED_ATTR, PARTICLE_ATTR, target_l=20)
    system = init_diamond_system(15, 0.966, 1, BONDED_ATTR, NON_BONDED_ATTR, PARTICLE_ATTR, target_l=20)
    N = 20
    
    #for i in range(N):
    #    system.part.add(pos = system.box_l*np.random.random(3), **PARTICLE_ATTR['cation'])
    #    system.part.add(pos = system.box_l*np.random.random(3), **PARTICLE_ATTR['anion'])
    #    minimize_energy(system, timeout=5)
    #system.analysis.pressure()['total']
    #print(system.box_l)
#%%
    from espressomd.visualization_opengl import  openGLLive
    visualizer = openGLLive(system)
    visualizer.run()
# %%
