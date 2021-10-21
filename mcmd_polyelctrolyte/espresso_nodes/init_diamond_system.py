"""
The script here is used to espressomd.System with a cross-linked polymer chain (gel).
The gel has some of the monomers ionized, ionized monomers position are random. 
The number of ionized monomers is defined by alpha = N_ion/N_all.
During the generation process counter-ions for the ionized monomers will be created. 
"""

import sys
import espressomd
import numpy as np
import random
import logging

def init_diamond_system(MPC, bond_length, alpha, target_l, bonded_attr, non_bonded_attr, particle_attr):
    from espressomd import diamond
    a = (MPC + 1) * bond_length / (0.25 * np.sqrt(3))
    box_l = [a]*3
    system = espressomd.System(box_l = box_l)
    system.time_step = 0.001
    system.cell_system.skin = 0.4
    system.thermostat.set_langevin(kT=1, gamma=1, seed=42)
    system.minimize_energy.init(f_max=50, gamma=60.0, max_steps=10000, max_displacement=0.001)

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
        diamond.Diamond(a=a, bond_length=bond_length, MPC=MPC)
    else:
        for i in range(MPC*16+8):
            logging.debug(
                f"bonded interaction is not setup, no net created")
            system.part.add(pos = system.box_l*np.random.random(3), **particle_attr['gel_neutral'])
    gel_indices  = (start_id+1, system.part.highest_particle_id+1)

    re_type_nodes(system, gel_indices, particle_attr)
    charge_gel(system, gel_indices, alpha, particle_attr)
    logging.debug('Minimizing energy before volume change')
    system.minimize_energy.minimize()
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

def change_volume(system, target_l, scale_down_factor = 0.97, scale_up_factor = 1.05, integrator_steps = 10000):
    logging.debug (f'change_volume to the size L = {target_l}')
    while system.box_l[0] != target_l:
        factor = target_l/system.box_l[0]
        if factor<scale_down_factor: 
            factor = scale_down_factor 
        elif factor>scale_up_factor:
            factor = scale_up_factor
        d_new = system.box_l[0]*factor
        system.change_volume_and_rescale_particles(d_new)
        system.integrator.run(integrator_steps)
        logging.debug(f'gel box_size: {system.box_l[0]}')
        logging.debug(f"pressure: {system.analysis.pressure()['total']}")
    logging.debug ('volume change done')

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



if __name__=='__main__':
    from shared import PARTICLE_ATTR, BONDED_ATTR, NON_BONDED_ATTR
    #BONDED_ATTR = None
    #NON_BONDED_ATTR = None
    system = init_diamond_system(15,0.966,0.5,30, BONDED_ATTR, NON_BONDED_ATTR, PARTICLE_ATTR)
    N = 30
    for i in range(N):
        system.part.add(pos = system.box_l*np.random.random(3), **PARTICLE_ATTR['cation'])
        system.part.add(pos = system.box_l*np.random.random(3), **PARTICLE_ATTR['anion'])
        system.integrator.run(10000)
    system.analysis.pressure()['total']
    from espressomd.visualization_opengl import  openGLLive
    visualizer = openGLLive(system)
    visualizer.run()