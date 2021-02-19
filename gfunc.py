import os, sys
import numpy as np

from gel import gel
from gibbs_params import *


def gfunc(qi,qo):

    # ~ sys.stdout = open(str(os.getpid()) + ".out", "w")
    #sys.stdout = open("gfunc.out", "w", buffering=1)
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
