import os, sys
import numpy as np

from gel import gel
from gibbs_params import *


def gfunc(qi,qo):

    # ~ sys.stdout = open(str(os.getpid()) + ".out", "w")
    sys.stdout = open("gfunc.out", "w", buffering=1)
    print('strating gfunc')
    g =gel()
    g.lB = 0.0
    g.eq_steps = 100
    g.sigma = 1.0
    #g.swap = True
    g.exclusion_radius = 1.0
    g.box_l = 80.5
    g.cs = cs = 0.06
    g.p['Cl'] = -np.log10(cs)
    g.eq_steps = 10
    #g.steps['md'] = 64
    #g.steps['re'] = 32
    
    #g.p['Na'] = -np.log10(cs)

    g.p['Na'] = -np.log10(cs*0.873)
    g.p['Ca'] = -np.log10(cs*0.114)    
    
    g.p['K'] = 3.0
    g.p['H'] = 7.0
    g.N_Samples = 200


    g.__str__() # this updates the filenames
    print(g) # this updates the filenames
    alpha_ini = g.get_alpha_ini()

    g.diamond(alpha = alpha_ini)
    g.system.setup_type_map(list(g.TYPES.values()))
    # ~ print(g.name)
    g.set_insertions()
    g.set_ionization()

    g.minimize_energy()
    g.set_thermostat()


    g.set_LJ()
    g.minimize_energy()
    g.change_volume(g.box_l)
    g.minimize_energy()

    g.equilibrate(eq_steps = 10)
    for i in range (100): g.RE.reaction(reaction_steps = 100); print(g.getN(g.keys['re']))

    g.set_EL()
    g.minimize_energy()

    g.equilibrate()

    choices = [g.sampleMD]*bool(g.sigma)+[g.sampleRE]*hasattr(g, 'RE'  )
    # if sigma is not zero then add 'pressure' to the list of mdkeys
    g.keys['md'] = ['Re']+['pressure']*bool(g.sigma)
    #a = 1
    #print('sampling gel', a ,' times')
    #for i in range(a):    np.random.choice(choices)()
    
    Eini = g.energy()
    NClgel = g.system.number_of_particles(g.TYPES['Cl'])   
    NNagel = g.system.number_of_particles(g.TYPES['Na'])   
    N = [NClgel, NNagel]
    DE = 0
    V = g.volume
    g.current_state = [DE, V, N]
    qo.put([DE, V, N])
    while True:
        xi = qi.get()
        # ~ print ('gfunc xi', xi)
        Eini = g.energy()
        if xi>0:
            try:
                pair = g.removePair()
            except ValueError:
                pass
        else:
            pair = g.addPair()
        NCl = g.system.number_of_particles(g.TYPES['Cl'])   
        NNa= g.system.number_of_particles(g.TYPES['Na'])   
        N = [NCl, NNa]
        DE = Eini - g.energy() 
        V = g.volume
        qo.put([DE, V, N])
        # ~ print ('gel parts', g.system.part[:].type)
        print ('Cl particles in gel', NCl, 'gel volume', V)
        accept = qi.get()
        if accept:
            g.current_state = [DE, V, N]
            # ~ qo.put(g.current_state)
        else:
            # ~ qo.put(g.current_state)
            if xi>0:
                [aid, apos, av, atype, aq] = pair[0]
                [bid, bpos, bv, btype, bq] = pair[1]
                g.system.part.add(pos=apos, type=atype, q=aq, v=av)
                g.system.part.add(pos=bpos, type=btype, q=bq, v=bv)
            else:
                [a,b] = pair
                a.remove()
                b.remove()
