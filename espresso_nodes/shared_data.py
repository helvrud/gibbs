#%%
ELECTROSTATIC = False
V_all = 20**3*2
v = 0.5 #relative volume of the box with fixed anions
#box volumes and dimmensions
V = [V_all*(1-v),V_all*v]
box_l = [V_**(1/3) for V_ in V]
l_bjerrum = 2.0
temp = 1
ELECTROSTATIC = False
N1 = 100 #mobile ions on the left side
N2 = 100 #mobile ions on the right side



MOBILE_SPECIES_COUNT = [
        {'anion' : int(N1/2), 'cation' : int(N1/2)}, #left side
        {'anion' : int(N2/2), 'cation' : int(N2/2)}, #right side
    ]



#attributes to use when creating
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
from itertools import combinations
lj_sigma=1
NON_BONDED_ATTR = {
    pair : dict(epsilon=1, sigma=lj_sigma, cutoff=lj_sigma*2**(1./6), shift='auto')
    for pair in (combinations([ATTR['type'] for ATTR in PARTICLE_ATTR.values()], 2))
}

#FENE
BONDED_ATTR = {
    'FeneBond' : dict(k=30, d_r_max=2.0, r_0 = 0.0)
}

#DIAMOND_GEL ATTRS
DIAMOND_ATTR = dict(
    bond_length=0.966, 
    MPC=15,
    )