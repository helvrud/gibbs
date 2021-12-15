import os, sys
import numpy as np

from salt import salt
from gibbs_params import *

def sfunc(qi,qo, Ns, Vs):



    # ~ sys.stdout = open(str(os.getpid()) + ".out", "w")
    sys.stdout = open("sfunc.out", "w", buffering=1)
    print('strating gfunc')
    s =salt()
    s.lB = 0.0
    s.eq_steps = 100
    s.sigma = 1.0
    #g.swap = True
    s.exclusion_radius = 1.0
    s.box_l = Vs**(1./3)
    s.cs = cs = 0.06
    s.p['Cl'] = -np.log10(cs)
    s.eq_steps = 100
    #g.steps['md'] = 64
    #g.steps['re'] = 32
    
    #g.p['Na'] = -np.log10(cs)

    s.p['Na'] = -np.log10(cs*0.873)
    s.p['Ca'] = -np.log10(cs*0.114)    
    
    s.N_Samples = 200


    s.__str__() # this updates the filenames
    print(s) # this updates the filenames
    import espressomd
    s.system = espressomd.System(box_l = [s.box_l]*3)
    #s.system.set_random_state_PRNG()

    s.system.time_step = s.time_step
    s.system.cell_system.skin = 0.4
    
    s.system.setup_type_map(list(s.TYPES.values()))
    # ~ print(g.name)
    s.set_insertions()


    s.minimize_energy()
    s.set_thermostat()


    s.set_LJ()
    s.minimize_energy()

    s.minimize_energy()

    s.equilibrate(eq_steps = 10)
    for i in range (100): s.RE.reaction(reaction_steps = 100); print(s.getN(s.keys['re']))

    s.set_EL()
    s.minimize_energy()

    s.equilibrate()

    choices = [s.sampleMD]*bool(s.sigma)+[s.sampleRE]*hasattr(s, 'RE'  )
    # if sigma is not zero then add 'pressure' to the list of mdkeys
    s.keys['md'] = ['Re']+['pressure']*bool(s.sigma)
    #a = 1
    #print('sampling gel', a ,' times')
    #for i in range(a):    np.random.choice(choices)()
    
    Eini = s.energy()
    NClgel = s.system.number_of_particles(s.TYPES['Cl'])   
    NNagel = s.system.number_of_particles(s.TYPES['Na'])   
    N = [NClgel, NNagel]
    DE = 0
    V = Vs
    s.current_state = [DE, V, N]
    qo.put([DE, V, N])
    while True:
        xi = qi.get()
        # ~ print ('gfunc xi', xi)
        Eini = s.energy()
        if xi>0:
            try:
                pair = s.removePair()
            except ValueError:
                pass
        else:
            pair = s.addPair()
        NCl = s.system.number_of_particles(s.TYPES['Cl'])   
        NNa= s.system.number_of_particles(s.TYPES['Na'])   
        N = [NCl, NNa]
        DE = Eini - s.energy() 

        qo.put([DE, V, N])
        # ~ print ('gel parts', g.system.part[:].type)
        print ('Cl particles in gel', NCl, 'gel volume', V)
        accept = qi.get()
        if accept:
            s.current_state = [DE, V, N]
            # ~ qo.put(s.current_state)
        else:
            # ~ qo.put(s.current_state)
            if xi<0:
                [aid, apos, av, atype, aq] = pair[0]
                [bid, bpos, bv, btype, bq] = pair[1]
                g.system.part.add(pos=apos, type=atype, q=aq, v=av)
                g.system.part.add(pos=bpos, type=btype, q=bq, v=bv)
            else:
                [a,b] = pair
                a.remove()
                b.remove()






