import numpy as np
# ~ import os, sys
from multiprocessing import Process, Queue

from sfunc import sfunc
from gfunc import gfunc
from gibbs_params import *


siqueue = Queue()
soqueue = Queue()
qi = giqueue = Queue()
qo = goqueue = Queue()



gproc = Process(target=gfunc,  args=(giqueue,goqueue,))
gproc.start()
[DE, V, N] = goqueue.get()
[NClgel, NNagel] = N
NClsalt = NCl - NClgel
Ls = (L**3 - Lg**3)**(1./3)
sproc = Process(target=sfunc, args=(siqueue,soqueue, NClsalt, Ls))
sproc.start()

# ~ print(q.get())    # prints "[42, None, 'hello']"
# ~ for i in range(10):
while True:
    xi = np.random.choice([1,-1])
    giqueue.put(xi)
    [Eg, Vg, Ng] = goqueue.get()
    siqueue.put(xi)
    [Es, Vs, Ns] = soqueue.get()
    #  emulates heaviside function
    
    acceptance = -Es-Eg+xi*( np.log(Vs/Vg) + np.log((Ng[0]+np.heaviside(xi,0))/((Ns[0]+np.heaviside(-xi,0)))) + np.log((Ng[1]+np.heaviside(xi,0))/((Ns[1]+np.heaviside(-xi,0))) ))
    acceptance = np.exp(acceptance)
    accept = acceptance > np.random.rand()
    print(acceptance, accept)
    siqueue.put(accept)
    giqueue.put(accept)

# ~ print(q.get())
# ~ sproc.join()
# ~ gproc.join()
