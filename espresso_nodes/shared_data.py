
ELECTROSTATIC = False

N1 = 75*2 #mobile ions on the left side
N2 = 25*2 #mobile ions on the right side
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
)
#types of the particles that are mobile
MOBILE_SPECIES = [0,1]

#LJ
NON_BONDED_ATTR = {
    (0,0) : dict(epsilon=1, sigma=1, cutoff=3, shift='auto'),
    (0,1) : dict(epsilon=1, sigma=1, cutoff=3, shift='auto'),
    (0,2) : dict(epsilon=1, sigma=1, cutoff=3, shift='auto'),
    (0,3) : dict(epsilon=1, sigma=1, cutoff=3, shift='auto'),
    (1,1) : dict(epsilon=1, sigma=1, cutoff=3, shift='auto'),
    (1,2) : dict(epsilon=1, sigma=1, cutoff=3, shift='auto'),
    (1,3) : dict(epsilon=1, sigma=1, cutoff=3, shift='auto'),
    (2,2) : dict(epsilon=1, sigma=1, cutoff=3, shift='auto'),
    (2,3) : dict(epsilon=1, sigma=1, cutoff=3, shift='auto'),
    (3,3) : dict(epsilon=1, sigma=1, cutoff=3, shift='auto'),
}

#FENE
BONDED_ATTR = {
    'FeneBond' : dict(k=30, d_r_max=1.5)
}

#DIAMOND_GEL ATTRS
DIAMOND_ATTR = dict(
    bond_length=0.966, 
    MPC=15,
    )
