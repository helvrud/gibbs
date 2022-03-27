#%%
import espressomd
from routines import sample_to_target
import logging
logger = logging.getLogger(__name__)

def _minimize_energy(system):
    system.thermostat.suspend()
    system.integrator.set_steepest_descent(
    f_max=0, gamma=0.1, max_displacement=0.1)
    min_d = system.analysis.min_dist()
    logger.info(f"Minimal distance: {min_d}")
    while (min_d) < 0.5 or (min_d==np.inf):
        system.integrator.run(100)
        min_d = system.analysis.min_dist()
        logger.debug(f"Minimal distance: {min_d}")
    system.integrator.set_vv()
    system.thermostat.recover()
    system.integrator.run(10000)

def init_reservoir_system(box_l, non_bonded_attr):
    system = espressomd.System(box_l = [box_l]*3)
    system.time_step = 0.001
    system.cell_system.skin = 0.4
    system.thermostat.set_langevin(kT=1, gamma=1, seed=42)

    if non_bonded_attr is not None:
        logger.info(f"non-bonded provided")
        logger.info(non_bonded_attr)
        [system.non_bonded_inter[particle_types].lennard_jones.set_params(**lj_kwargs)
            for particle_types, lj_kwargs in non_bonded_attr.items()]
        logger.debug(f"non-bonded interaction is setup")

    logger.debug("Reservoir system initialized")
    system.setup_type_map([0,1,2,3,4,5])
    return system

if __name__=='__main__':
    from shared import NON_BONDED_ATTR
    import numpy as np
    system = init_reservoir_system(50, NON_BONDED_ATTR)
    n=100
    [system.part.add(
            pos=system.box_l * np.random.random(3), q=-1, type=0) for _ in range(n)
        ]
    [system.part.add(
            pos=system.box_l * np.random.random(3), q=+1, type=1) for _ in range(n)
        ]

    _minimize_energy(system)
    integrator_steps = 1000
    system.integrator.run(integrator_steps)

    #from espressomd import electrostatics
    #l_bjerrum = 2
    #p3m = electrostatics.P3M(prefactor=l_bjerrum, accuracy=1e-3)
    #system.actors.add(p3m)
    #p3m_params = p3m.get_params()
    #logger.debug(p3m_params)
    #_minimize_energy(system)
    #integrator_steps = 100000
    #system.integrator.run(integrator_steps)

    from espressomd.visualization_opengl import  openGLLive
    visualizer = openGLLive(system)
    visualizer.run()