#%%
from montecarlo.libmontecarlo import sample_to_target_error
import numpy as np
from ion_pair_monte_carlo import build_no_gel
from utils import sample_all
#%%
MC = build_no_gel(
    Volume=[20000,20000], 
    N_pairs=[100,100], 
    A_fixed = 50, 
    log_names=['box_0.log', 'box_1.log'],
    python_executable='pypresso',
    )
#%%
MC.equilibrate(rounds=5)
#%%
result = sample_all(MC, 5)
# %%
