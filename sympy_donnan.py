# %%
from sympy import Symbol, Eq, solve, sqrt, latex
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
c_s_0 = Symbol("c_s", positive=True)  # init salt conc
V_gel_0 = Symbol("V", positive=True)  # init salt conc
c_p =  Symbol("c_p", positive=True) # gel init molar volume
alpha =  Symbol("alpha", positive=True) # gel ionization degree
gamma =  Symbol("gamma", positive=True) # gel compression
Anions_gel_inf = sqrt(A_fixed**2 + 4*c_s_0**2*V_gel_0**2)/2 - A_fixed/2
Anions_gel_inf
#%%
Anions_gel.subs(N_pairs, c_s_0*V_gel_0)
# %%
(Anions_gel**2).simplify()
# %%
Anion_salt = N_pairs-Anions_gel
Anion_salt.simplify()
# %%
c_s=Anion_salt.subs(N_pairs, c_s_0*V_gel_0).subs(A_fixed, alpha*c_p*V_gel_0)/V_salt
c_s = c_s.simplify()
# %%
c_s_on_gamma = c_s.subs(V_gel, gamma*V_gel_0).subs(V_salt,(1-gamma)*V_gel_0).simplify()

# %%
c_s_on_gamma.subs(gamma,0)
# %%
print(latex(c_s_on_gamma))
# %%
c_s = c_s.subs(V_salt, V_gel_0 - V_gel).subs(c_p, 1/V_gel_0).simplify()
# %%
print(latex(c_s))
# %%
