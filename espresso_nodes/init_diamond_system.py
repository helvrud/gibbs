#%%
import espressomd
import numpy as np
import random
import logging
logger = logging.getLogger(__name__)

from shared_data import BONDED_ATTR, NON_BONDED_ATTR, PARTICLE_ATTR


def init_diamond_system(MPC, bond_length, alpha, target_l):
    from espressomd import diamond
    a = (MPC + 1) * bond_length / (0.25 * np.sqrt(3))
    box_l = [a]*3
    system = espressomd.System(box_l = box_l)
    system.time_step = 0.001
    system.cell_system.skin = 0.4
    system.thermostat.set_langevin(kT=1, gamma=1, seed=42)
    system.minimize_energy.init(f_max=50, gamma=60.0, max_steps=10000, max_displacement=0.001)

    logger.info(f"gel initial volume: {box_l}")
    fene = espressomd.interactions.FeneBond(**BONDED_ATTR['FeneBond'])
    system.bonded_inter.add(fene)
    setup_non_bonded(system, NON_BONDED_ATTR)
    
    start_id = system.part.highest_particle_id
    diamond.Diamond(a=a, bond_length=bond_length, MPC=MPC)
    gel_indices  = (start_id+1, system.part.highest_particle_id+1)
    
    re_type_nodes(system, gel_indices)
    charge_gel(system, gel_indices, alpha)
    system.minimize_energy.minimize()
    change_volume(system, target_l)
    return system

def setup_non_bonded(system, non_bonded_attr):
    [system.non_bonded_inter[particle_types].lennard_jones.set_params(**lj_kwargs)
            for particle_types, lj_kwargs in non_bonded_attr.items()]
    logger.debug('Non-bonded interaction is set')


def re_type_nodes(system, gel_indices):
    """
    espresso/src/core/diamond.cpp
    int const type_bond = 0; first 8 nodes
    int const type_node = 0;
    int const type_cM = 1;
    int const type_nM = 1;
    int const type_CI = 2;
    """ 
    N_NODES = 8
    particles = list(system.part[slice(*gel_indices)])
    for i, part in enumerate(particles):
        if i<8:
            for attr_name, attr_val in PARTICLE_ATTR['gel_node_neutral'].items():
                setattr(part, attr_name, attr_val)
        else:
            for attr_name, attr_val in PARTICLE_ATTR['gel_neutral'].items():
                setattr(part, attr_name, attr_val)
    logger.debug('Gel particles types is set')

def charge_gel(system, gel_indices, alpha, add_counterions = True):
    particles = list(system.part[slice(*gel_indices)])
    n_charged = int(len(particles)*alpha)
    logger.info(f'Charging the gel...')
    for i, part in enumerate(random.sample(particles, n_charged)):
        if part.type == PARTICLE_ATTR['gel_neutral']['type']:
            for attr_name, attr_val in PARTICLE_ATTR['gel_anion'].items():
                setattr(part, attr_name, attr_val)
        else: #part.type == PARTICLE_ATTR['gel_']:
            for attr_name, attr_val in PARTICLE_ATTR['gel_node_anion'].items():
                setattr(part, attr_name, attr_val)
        if add_counterions:
            system.part.add(pos = system.box_l*np.random.random(3), **PARTICLE_ATTR['cation'])
        logger.debug(f'{i}/{n_charged} charged')

def change_volume(system, target_l, scale_down_factor = 0.97, scale_up_factor = 1.05, integrator_steps = 10000):
    logger.info(f'Changing the box_l to target value: {target_l}')
    while system.box_l[0] != target_l:
        factor = target_l/system.box_l[0]
        if factor<scale_down_factor: 
            factor = scale_down_factor 
        elif factor>scale_up_factor:
            factor = scale_up_factor
        d_new = system.box_l[0]*factor
        system.change_volume_and_rescale_particles(d_new)
        system.integrator.run(integrator_steps)
        logger.info(f'Current box_size: {system.box_l[0]}')
    print ('volume change done')

def zero_pressure_volume(system, scale_down_factor = 0.97, scale_up_factor = 1.05, integrator_steps = 10000, eps = 0.001):
    pass

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
#%%
if __name__=='__main__':
    system = init_diamond_system(15,0.966,0.1,20)
#%%    
    system.analysis.pressure()['total']
    from espressomd.visualization_opengl import  openGLLive
    visualizer = openGLLive(system)
    visualizer.run()
#%%
    import espressomd.observables
    pressure = espressomd.observables.Observable.Pressure()# %%

# %%
    espressomd.observables.Observable.__dir__
# %%
