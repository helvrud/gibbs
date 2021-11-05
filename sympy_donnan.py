#%%
from sympy import Symbol, Eq, solve
#KNOWN
N_pairs= Symbol("N_pairs", positive = True) #number of all particles
#v= Symbol("v", positive = True) #relative volume of the gel
A_fixed = Symbol("A_fix", positive = True) #fixed anion conc
V_salt = Symbol("V_salt", positive = True) #salt box volume
V_gel = Symbol("V_gel", positive = True) #gel box volume
#UNKNOWN
A_salt = Symbol("A_salt", positive = True) #salt anions conc
A_gel = Symbol("A_gel", positive = True) #gel anions conc
# %%
x = Symbol('x')
mass_law = Eq(((N_pairs-x)/V_salt)**2, x*(A_fixed+x)/V_gel**2)
#mass_law = mass_law.subs(V_gel, V_salt).simplify()
mass_law
#%%
x_solved = solve(mass_law, x)[0]
x_solved
#%%
A_salt_conc = (N_pairs-x_solved)/V_salt
A_gel_conc = (A_fixed+x_solved)/V_gel
zeta = A_gel_conc/A_salt_conc
#%%
v = Symbol('v')
zeta = zeta.subs(V_salt, 1-v).subs(V_gel,v)
#%%
zeta
#%%
from sympy import limit
limit(zeta, v, 0.5)
#%%
from sympy import lambdify
f = lambdify([N_pairs, A_fixed, v], zeta, "numpy")
# %%
import sympy
import matplotlib.pyplot as plt
import numpy as np
vv = np.linspace(0.01,0.99)
V=1000
zetas = [1/f(200, 124, v_) for v_ in vv]
plt.plot(vv, zetas)
# %%
print(zeta)
# %%
print(zeta)
# %%
