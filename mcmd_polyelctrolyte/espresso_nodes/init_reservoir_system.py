import espressomd
import logging

def init_reservoir_system(box_l, non_bonded_attr):
    system = espressomd.System(box_l = [box_l]*3)
        
    system.time_step = 0.001
    system.cell_system.skin = 0.4
    system.thermostat.set_langevin(kT=1, gamma=1, seed=42)
    system.minimize_energy.init(f_max=50, gamma=30.0, max_steps=10000, max_displacement=0.01)

    if non_bonded_attr is not None:
        setup_non_bonded(system, non_bonded_attr)
        logging.debug(f"non-bonded interaction is setup")

    logging.debug("Reservoir system initialized")
    system.minimize_energy.minimize()
    
    return system

def setup_non_bonded(system, non_bonded_attr):
    [system.non_bonded_inter[particle_types].lennard_jones.set_params(**lj_kwargs)
            for particle_types, lj_kwargs in non_bonded_attr.items()]

if __name__=='__main__':
    from shared import NON_BONDED_ATTR
    import numpy as np
    NON_BONDED_ATTR = None
    system = init_reservoir_system(30, NON_BONDED_ATTR)
    n=100
    [system.part.add(
            pos=system.box_l * np.random.random(3)) for _ in range(n)
        ]
    system.minimize_energy.minimize()
    system.integrator.run(10000)
    from espressomd.visualization_opengl import  openGLLive
    visualizer = openGLLive(system)
    visualizer.run()