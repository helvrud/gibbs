#attributes to use when creating particles
PARTICLE_ATTR = dict(
    anion = {'type' : 0, 'q':-1},
    cation = {'type' : 1, 'q':1},
    gel_neutral = {'type' : 2, 'q':0},
    gel_anion = {'type' : 3, 'q':-1},
    gel_node_neutral = {'type' : 4, 'q':0},
    gel_node_anion = {'type' : 5, 'q':0}, # The nodes are always neutral
)
#types of the particles that are mobile
MOBILE_SPECIES = [0,1]

#LJ
from itertools import combinations_with_replacement

# Avogadro number
Navogadro = 6.022e23 # 1/mol
kT = 1.38064852e-23*300 # J
epsilon = 1.0 # kT
sigma = 1.0 # esunits
unit_of_length = sigma_SI = 0.35 # nm
unit = (unit_of_length*1e-9)**3*Navogadro*1000 # l/mol
punit = kT*Navogadro/(unit/1000) # J/m3 = Pa

NON_BONDED_ATTR = {
    pair : dict(epsilon=epsilon, sigma=sigma, cutoff=sigma*2**(1./6), shift='auto')
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
