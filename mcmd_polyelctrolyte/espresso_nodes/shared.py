#attributes to use when creating particles
PARTICLE_ATTR = dict(
    anion = {'type' : 0, 'q':-1},
    cation = {'type' : 1, 'q':1},
    gel_neutral = {'type' : 2, 'q':0},
    gel_anion = {'type' : 3, 'q':-1},
    gel_node_neutral = {'type' : 4, 'q':0},
    gel_node_anion = {'type' : 5, 'q':-1},
)
#types of the particles that are mobile
MOBILE_SPECIES = [0,1]

#LJ
from itertools import combinations_with_replacement
lj_sigma=1
NON_BONDED_ATTR = {
    pair : dict(epsilon=1, sigma=lj_sigma, cutoff=lj_sigma*2**(1./6), shift='auto')
    for pair in (combinations_with_replacement([ATTR['type'] for ATTR in PARTICLE_ATTR.values()], 2))
}

#FENE
BONDED_ATTR = {
    'FeneBond' : dict(k=10, d_r_max=2.0, r_0 = 0.0)
}

#DIAMOND_GEL ATTRS
DIAMOND_ATTR = dict(
    bond_length=0.966,
    MPC=15,
    )