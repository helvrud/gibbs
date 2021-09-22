#%%
from donnan_analytic import zeta
from sympy import Symbol, Eq, solve, sqrt
#known
N_pair= Symbol("N_pair", positive = True) #number of all particles
v= Symbol("v", positive = True) #relative volume of the gel
A_fixed = Symbol("A_fix", positive = True) #number of fixed anions
#unknown
A_salt = Symbol("A_salt", positive = True) #number of mobile anions in salt
A_gel = Symbol("A_gel", positive = True) #number of mobile anions in gel
# %%
mass_law = Eq(A_salt**2/(1-v)**2, A_gel*(A_gel+A_fixed)/v**2)
mass_law
#%%
number_of_particle_eq = Eq(N_pair, A_gel + A_salt)
number_of_particle_eq
#%%
A_gel_root = solve(number_of_particle_eq, A_gel)[0]
A_salt_root = solve(mass_law.subs(A_gel, A_gel_root), A_salt)[0]
#%%
A_gel_root
#%%
result = solve([mass_law, number_of_particle_eq], A_salt, A_gel)
#%%
possible_zeta = [(result_[1]/result_[0]/(v/(1-v))).simplify() for result_ in result]
#%%
possible_zeta[0]
#%%
print(possible_zeta[0])
#%%
from sympy import lambdify
f = lambdify([N_pair, v, A_fixed],possible_zeta[0],"numpy")
# %%
import matplotlib.pyplot as plt
import numpy as np
vv = np.linspace(0.01,0.99)
zetas = [f(200, v_, 248) for v_ in vv]
plt.plot(vv, zetas)
# %%
f
# %%
