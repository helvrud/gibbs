#%%
from sympy import Symbol, Eq, solve, sqrt

N= Symbol("N", positive = True) #number of all particles
v= Symbol("v", positive = True) #relative volume of the gel
A_fixed = Symbol("A_fix", positive = True) #number of fixed anions
# %%
A_gel= Symbol("A_gel", positive = True) #number of mobile anions
solve_eq = Eq(2*sqrt(A_gel**2+A_gel*A_fixed)*(1-v)/v + 2*A_gel + A_fixed,N)
#%%
A_gel_root = solve(solve_eq, A_gel)
# %%
r=A_gel_root[1]
r
# %%
def A_gel_func(N, A_fix, v):
    import numpy as np
    sqrt = np.sqrt
    if v != 0.5:
        return (-2*A_fix*v + A_fix + N*v**2 + (v-1)*sqrt(-2*A_fix**2*v + A_fix**2 + N**2*v**2))/(2*(2*v - 1))
    else:
        return (A_fix**2 + N*(-2.0*A_fix + N))/N/4
# %%
A_gel_func(324,124,0.5)
# %%
def r(N, A_fix, v):
    import numpy as np
    a_gel = A_gel_func(N, A_fix, v)
    return np.sqrt(a_gel**2-a_gel*A_fix)/a_gel
# %%
r(200,24,0.5)
# %%
import sympy
# %%
dV = sympy.Symbol('\Delta V')
x = sympy.Symbol('x', positive = True)
dx = sympy.Symbol('\Delta x')
# %%
eq = sympy.Eq((x+dx)**3-x**3, dV)
eq
# %%
dx_r = sympy.solve(eq, dx)
# %%
print(dx_r[2].simplify())
# %%
def dx(x, V):
    import numpy as np
    sqrt = np.sqrt
    return -x - 2**(2/3)*(-V - x**3 + sqrt((V + x**3)**2))**(1/3)/2

# %%
dx(10,1)
# %%
