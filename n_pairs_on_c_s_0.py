"""
The script prepares data from gibbs and grandcanonical ensembles
"""

#%%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
#matplotlib settings
LAST_USED_COLOR = lambda: plt.gca().lines[-1].get_color()
plt.rcParams['axes.xmargin'] = 0
plt.rcParams['axes.ymargin'] = 0

from mcmd_polyelctrolyte.utils import n_to_mol

gibbs_data_path = "data/gel_all_data.pkl"
gc_data_path = "data/GC.pkl"

gibbs_raw = pd.read_pickle(gibbs_data_path)
gc_raw = pd.read_pickle(gc_data_path)
#%%
## pivot the raw data, from flat table to the one with lists in the cells
gibbs_raw['V'] = gibbs_raw.v*gibbs_raw.V0
gibbs_raw['c_gel'] = gibbs_raw.fixed_anions/gibbs_raw.V
gibbs_raw['box_l'] = gibbs_raw.V**(1/3)
gibbs_pivot = pd.pivot_table(
    gibbs_raw, 
    index =  ['n_pairs', 'V0', 'fixed_anions'], 
    values = [
        #'v',
        'V',
        'gel_density',
        #'zeta_mean', 
        'c_s_mol_mean', 
        'delta_P_Pa_mean', 
        #'cation_salt_mean',
        #'anion_salt_mean'
        ],
    aggfunc = list).reset_index()

gibbs_pivot.rename(columns={'c_s_mol_mean' : 'cs', 'delta_P_Pa_mean' : 'P'}, inplace=True)
# %%
