#%%
from donnan_analytic import zeta
from sympy import Symbol, Eq, solve, sqrt

N= Symbol("N", positive = True) #number of all particles
v= Symbol("v", positive = True) #relative volume of the gel
A_fixed = Symbol("A_fix", positive = True) #number of fixed anions
#unknown
A_salt = Symbol("A_salt", positive = True) #number of mobile anions in salt
A_gel = Symbol("A_gel", positive = True) #number of mobile anions in gel
# %%
mass_law = Eq(A_salt**2/(1-v)**2, A_gel*(A_gel+A_fixed)/v**2)
mass_law
#%%
number_of_particle_eq = Eq(N, A_fixed + 2*A_gel + 2*A_salt)
number_of_particle_eq
#%%
result = solve([mass_law, number_of_particle_eq], A_salt, A_gel)
#%%
possible_zeta = [(result_[1]/result_[0]/(v/(1-v))).simplify() for result_ in result]
#%%
possible_zeta[0]
#%%
print(possible_zeta[0])
#%%
def zeta(N,v,A_fix):
    return (-2*A_fix*v + A_fix + N*v**2 + v*sqrt(-2*A_fix**2*v + A_fix**2 + N**2*v**2) - sqrt(-2*A_fix**2*v + A_fix**2 + N**2*v**2))/(v*(N*v - N + sqrt(-2*A_fix**2*v + A_fix**2 + N**2*v**2)))
#%%
from sympy import lambdify
f = lambdify([N, v, A_fixed],possible_zeta[1],"numpy")
# %%
f(200, 0.3, 0)
# %%
import matplotlib.pyplot as plt
import numpy as np
vv = np.linspace(0.2,0.8)
zetas = [zeta(250, v_, 50) for v_ in vv]
plt.plot(vv, zetas)
# %%
f
# %%
