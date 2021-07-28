#%%
import sys
from shared_data import *
import espressomd
import numpy as np
import random

def init_diamond_system(MPC, bond_length, alpha):
    from espressomd import diamond
    a = (MPC + 1) * bond_length / (0.25 * np.sqrt(3))
    box_l = [a]*3
    system = espressomd.System(box_l = box_l)
    print(f"espressomd.System({box_l})")
    fene = espressomd.interactions.FeneBond(**BONDED_ATTR['FeneBond'])
    system.bonded_inter.add(fene)
    start_id = system.part.highest_particle_id
    diamond.Diamond(a=a, bond_length=bond_length, MPC=MPC)
    gel_indices  = (start_id+1, system.part.highest_particle_id+1)
    charge_gel(system, gel_indices, alpha)
    return system

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
