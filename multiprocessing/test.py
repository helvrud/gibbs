import numpy as np
# ~ import os, sys
from multiprocessing import Process, Queue
from espressomd import reaction_ensemble
from sfunc import sfunc
from gfunc import gfunc
from gibbs_params import *

import os, sys
import numpy as np

from gel import gel
from gibbs_params import *

siqueue = Queue()
soqueue = Queue()
qi = giqueue = Queue()
qo = goqueue = Queue()



g = gel()

g.box_l = Lg
g.p['K'] = 7
g.p['Na'] = -np.log10(0.15)

g.p['Cl'] = g.p['Na']
g.p['H'] = 7.0
g.p['Ca'] = np.infty

g.N_Samples = 10
g.eq_steps = 10
g.lB = lB
g.sigma = sigma


g.__str__() # this updates the filenames

alpha_ini = g.get_alpha_ini()
g.diamond(alpha = alpha_ini)
g.system.setup_type_map(list(g.TYPES.values()))



g.set_insertions()
g.set_ionization()

g.minimize_energy()
g.set_thermostat()

g.set_LJ()
g.minimize_energy()


g.change_volume(self.box_l)
g.minimize_energy()


g.equilibrate(eq_steps = 10)
for i in range (100): g.RE.reaction(reaction_steps = 10000); print(g.getN(g.keys['re']))


g.set_EL()
g.minimize_energy()


g.equilibrate()
g.sample()


g.Pearson(keys = g.keys['md']+g.keys['re'])
g.uptime = time.time() - tini
g.save()

































