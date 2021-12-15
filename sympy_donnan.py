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
