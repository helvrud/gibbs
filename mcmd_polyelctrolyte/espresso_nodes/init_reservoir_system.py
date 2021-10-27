import espressomd
import logging

def init_reservoir_system(box_l, non_bonded_attr):
    system = espressomd.System(box_l = [box_l]*3)
        
    system.time_step = 0.001
    system.cell_system.skin = 0.4
    system.thermostat.set_langevin(kT=1, gamma=1, seed=42)
    system.minimize_energy.init(f_max = 10, gamma = 10, max_steps = 2000, max_displacement= 0.1)

    if non_bonded_attr is not None:
        setup_non_bonded(system, non_bonded_attr)
        logging.debug(f"non-bonded interaction is setup")

    logging.debug("Reservoir system initialized")
    system.minimize_energy.minimize()

    integrator_steps = 100000
    system.integrator.run(integrator_steps)

    return system

def setup_non_bonded(system, non_bonded_attr):
    [system.non_bonded_inter[particle_types].lennard_jones.set_params(**lj_kwargs)
            for particle_types, lj_kwargs in non_bonded_attr.items()]

if __name__=='__main__':
    from shared import NON_BONDED_ATTR
    import numpy as np
    NON_BONDED_ATTR = None
    system = init_reservoir_system(50, NON_BONDED_ATTR)
    n=100
    [system.part.add(
            pos=system.box_l * np.random.random(3), q=-1, type=0) for _ in range(n)
        ]
    [system.part.add(
            pos=system.box_l * np.random.random(3), q=+1, type=1) for _ in range(n)
        ]
    system.minimize_energy.minimize()
    system.integrator.run(10000)

    from espressomd import electrostatics
    l_bjerrum = 2
    p3m = electrostatics.P3M(prefactor=l_bjerrum, accuracy=1e-3)
    system.actors.add(p3m)
    p3m_params = p3m.get_params()
    logging.debug(p3m_params)
    system.minimize_energy.minimize()
    integrator_steps = 100000
    system.integrator.run(integrator_steps)
    
    from espressomd.visualization_opengl import  openGLLive
    visualizer = openGLLive(system)
    visualizer.run()