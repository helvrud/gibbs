#%%
import sys
from shared_data import *
import espressomd
import numpy as np
import random

def init_diamond_system(MPC, bond_length, alpha, target_l):
    from espressomd import diamond
    a = (MPC + 1) * bond_length / (0.25 * np.sqrt(3))
    box_l = [a]*3
    system = espressomd.System(box_l = box_l)
    system.time_step = 0.001
    system.cell_system.skin = 0.4
    system.thermostat.set_langevin(kT=1, gamma=1, seed=42)
    system.minimize_energy.init(f_max=50, gamma=30.0, max_steps=10000, max_displacement=0.001)
    system.minimize_energy.minimize()
    system.integrator.run(10000)
    
    print(f"gel initial volume: {box_l}")
    fene = espressomd.interactions.FeneBond(**BONDED_ATTR['FeneBond'])
    system.bonded_inter.add(fene)
    setup_non_bonded(system, NON_BONDED_ATTR)
    
    start_id = system.part.highest_particle_id
    diamond.Diamond(a=a, bond_length=bond_length, MPC=MPC)
    gel_indices  = (start_id+1, system.part.highest_particle_id+1)
    charge_gel(system, gel_indices, alpha)
    change_volume(system, target_l)

    return system

def setup_non_bonded(system, non_bonded_attr):
    [system.non_bonded_inter[particle_types].lennard_jones.set_params(**lj_kwargs)
            for particle_types, lj_kwargs in non_bonded_attr.items()]

def charge_gel(system, gel_indices, alpha, add_counterions = True):
    #discharge the gel
    particles = list(system.part[slice(*gel_indices)])
    for part in particles:
        for attr_name, attr_val in PARTICLE_ATTR['gel_neutral'].items():
            setattr(part, attr_name, attr_val)
    #charge n_charged random particles
    n_charged = int(len(particles)*alpha)
    for part in random.sample(particles, n_charged):
        for attr_name, attr_val in PARTICLE_ATTR['gel_anion'].items():
            setattr(part, attr_name, attr_val)
    if add_counterions:
        for _ in range(n_charged):
            system.part.add(pos = system.box_l * np.random.random(3), **PARTICLE_ATTR['cation'])
    system.minimize_energy.minimize()
    system.integrator.run(10000)

def change_volume(system, target_l, scale_down_factor = 0.98, scale_up_factor = 1.05, integrator_steps = 10000):
    print ('change_volume to the size L = ', target_l)
    #~ target_l = self.box_l
    box_l = system.box_l[0]
    
    while box_l != target_l:
        if target_l < box_l:    
            print ('compression to box_l = ', box_l)
            box_l = box_l*scale_down_factor
            if box_l<target_l: box_l = target_l
        else:
            print ('blowing up to box_l = ', box_l)
            box_l = box_l*scale_down_factor
            if box_l>target_l: box_l = target_l
        system.change_volume_and_rescale_particles(d_new = box_l)
        system.minimize_energy.minimize()
        system.integrator.run(10000)
    print ('volume change done')
