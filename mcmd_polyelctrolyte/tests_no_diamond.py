#%%
import numpy as np
from ion_pair_monte_carlo import MonteCarloPairs, build_no_gel

#%%

MC = build_no_gel([20000,20000], [100,100], 50, ['box_0.log', 'box_1.log'])
#MC.equilibrate()
# %%
server = MC.server
# %%
server("system.part.select(q=0)", 0).result()
# %%
