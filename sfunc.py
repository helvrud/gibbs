import os, sys
import numpy as np

from salt import salt
from gibbs_params import *

def sfunc(qi,qo, Ns, Ls):
    # ~ sys.stdout = open(str(os.getpid()) + ".out", "w")
    sys.stdout = open("sfunc.out", "w", buffering=1)
    s = salt()

    s.box_l = Ls
    s.volume = Ls**3
    s.p['Na'] = -np.log10(0.15)
    s.p['Cl'] = s.p['Na']

    s.N_Samples = 10
    s.eq_steps = 10
    s.lB = lB
    s.sigma = sigma


    s.__str__() # this updates the filenames
    s.init_es()
    
    
    
    # ~ s.set_insertions(part_types = ['Na', 'Cl'])
    
    s.system.setup_type_map(s.TYPES.values() )
    
    
    
    for i in range(Ns):
        pos = np.random.random(3) * s.box_l
        s.system.part.add(pos=pos, type=s.TYPES['Cl'], q=s.val['Cl'])
        pos = np.random.random(3) * s.box_l
        s.system.part.add(pos=pos, type=s.TYPES['Na'], q=s.val['Na'])
    # ~ N = s.getN(keys = ['Na'])

    

    s.set_LJ()
    s.equilibrate()
    s.set_EL()
    s.equilibrate()

    choices = [s.sampleMD]*bool(s.sigma)+[s.sampleRE]*hasattr(s, 'RE'  )
    # if sigma is not zero then add 'pressure' to the list of mdkeys
    s.keys['md'] = ['Re']+['pressure']*bool(s.sigma)
    #a = 1
    #print('sampling salt', a ,' times')
    #for i in range(a):    np.random.choice(choices)()
    
    Eini = s.energy()
    NCl = s.system.number_of_particles(s.TYPES['Cl'])   
    NNa= s.system.number_of_particles(s.TYPES['Na'])   
    N = [NCl, NNa]
    DE = 0
    V = s.volume
    s.current_state = [DE, V, N]
    
    while True:
        xi = qi.get()
        # ~ print ('sfunc xi', xi)
        Eini = s.energy() 
        if xi<0:
            # here pair is type list of list [aid, apos, av, atype, aq]
            pair = s.removePair()
            #try:

            #except ValueError:
            #    pass
        else:
            # here pair is type list of espresso particles
            pair = s.addPair()
        NCl = s.system.number_of_particles(s.TYPES['Cl'])   
        NNa = s.system.number_of_particles(s.TYPES['Na'])   
        N = [NCl, NNa]
        E = Eini - s.energy() 
        V = s.volume
        qo.put([E, V, N])
        print ('Cl particles in salt', NCl, 'salt volume', round(V))
        accept = qi.get()
        if accept:
            s.current_state = [E, V, N]
            # ~ qo.put(s.current_state)
        else:
            # ~ qo.put(s.current_state)
            if xi<0:
                [aid, apos, av, atype, aq] = pair[0]
                [bid, bpos, bv, btype, bq] = pair[1]
                s.system.part.add(pos=apos, type=atype, q=aq, v=av)
                s.system.part.add(pos=bpos, type=btype, q=bq, v=bv)
            else:
                [a,b] = pair
                a.remove()
                b.remove()

