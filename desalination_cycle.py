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
gc_data_path = "data/GC.data"

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
#gibbs_pivot['c_s0'] = n_to_mol(gibbs_pivot.n_pairs/gibbs_pivot.V0)
# %%
#remove error for now
gc_raw.P = gc_raw.P.apply(lambda _: _[0])
#%%
#approx n_pairs used in further gibbs ensemble
gc_raw['n_pairs'] = round(gc_raw.Ncl_eq)
gc_raw['n_pairs'] = gc_raw['n_pairs'].astype(int)
# %%

#%%
fig, ax = plt.subplots()
#ax.set_yscale('log')
#ax.set_xscale('log')
for idx, grouped in gibbs_pivot.groupby(by = ['n_pairs', 'V0', 'fixed_anions']):
    ax.scatter(list(grouped.V), list(grouped.P), label = idx[0])
ax.legend(title = 'n_pairs')
# %%
fig, ax = plt.subplots()
#ax.set_yscale('log')
#ax.set_xscale('log')
for idx, grouped in gc_raw.groupby(by = ['n_pairs']):
    ax.scatter(list(grouped.V), list(grouped.P), label = idx)
ax.legend(title = 'n_pairs')
# %%
