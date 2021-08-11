from shared_data import *
import espressomd

def init_reservoir_system(box_l):
    system = espressomd.System(box_l = [box_l]*3)
    setup_non_bonded(system, NON_BONDED_ATTR)
        
    system.time_step = 0.001
    system.cell_system.skin = 0.4
    system.thermostat.set_langevin(kT=1, gamma=1, seed=42)
    system.minimize_energy.init(f_max=50, gamma=30.0, max_steps=10000, max_displacement=0.001)
    system.minimize_energy.minimize()
    system.integrator.run(10000)
    
    print("Reservoir system initialized")
    return system

def setup_non_bonded(system, non_bonded_attr):
    [system.non_bonded_inter[particle_types].lennard_jones.set_params(**lj_kwargs)
            for particle_types, lj_kwargs in non_bonded_attr.items()]
