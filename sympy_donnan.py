# %%
from sympy import Symbol, Eq, solve
# KNOWN
N_pairs = Symbol("N_pairs", positive=True)  # number of all particles
# v= Symbol("v", positive = True) #relative volume of the gel
A_fixed = Symbol("A_fix", positive=True)  # fixed anion conc
V_salt = Symbol("V_salt", positive=True)  # salt box volume
V_gel = Symbol("V_gel", positive=True)  # gel box volume
# UNKNOWN
# A_salt = Symbol("A_salt", positive = True) #salt anions conc
# A_gel = Symbol("A_gel", positive = True) #gel anions conc
# %%
x = Symbol('x')  # anions and counterion cations in gel
mass_law = Eq(((N_pairs-x)/V_salt)**2, x*(A_fixed+x)/V_gel**2)
#mass_law = mass_law.subs(V_gel, V_salt).simplify()
mass_law
# %%
Anions_gel = solve(mass_law, x)[0]
Anions_gel
# %%
print(Anions_gel)
#%%
c_s_0 = Symbol("c_s0", positive=True)  # init salt conc
V_gel_0 = Symbol("V_gel0", positive=True)  # init salt conc
v = Symbol("v", positive=True)  # compression
c_gel_0 = Symbol("c_gel0", positive=True)
c_gel = Symbol("c_salt", positive=True)
c_s_reservoir = Symbol("c_salt^reservoir", positive=True)

#%%
Anions_gel.subs(N_pairs, c_s_0*V_gel_0)
# %%
