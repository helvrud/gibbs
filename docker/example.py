#!espresso/es-build/pypresso
#!espresso/es-build/pypresso
import sys, os
os.chdir('/home/kvint/mv')
sys.path.append('/home/kvint/mv')
from espressomd import reaction_ensemble
from gel import gel
from numpy import inf
g =gel()
g.lB = 2.0
g.sigma = 1.0
g.epsilon = 1.0
g.box_l = 15.0
g.eq_steps = 10000
g.p['Cl'] = 0.8239087409443188
g.p['Na'] = 0.8828944972387491
g.p['Ca'] = 1.7670038896078462
g.p['K'] = inf
g.p['H'] = 7.0
g.N_Samples = 200
g.run()
