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
#gibbs_pivot['c_s0'] = n_to_mol(gibbs_pivot.n_pairs/gibbs_pivot.V0)
# %%
#remove error for now
gc_raw.P = gc_raw.P.apply(lambda _: _[0])
#%%
#approx n_pairs used in further gibbs ensemble
gc_raw['n_pairs'] = round(gc_raw.Ncl_eq)
gc_raw['n_pairs'] = gc_raw['n_pairs'].astype(int)
gc_raw.V = gc_raw.box_l**3
# %%
gc_raw = gc_raw.sort_values(by = "Ncl_eq")
#%%
#gc_raw.c_s_rounded = gc_raw.cs.apply(round)
gc_to_plot = gc_raw.iloc[2]
gibbs_to_plot = gibbs_pivot.iloc[[2,10]]

#%%
fig, ax = plt.subplots()
#ax.set_yscale('log')
#ax.set_xscale('log')
#for idx, grouped in gibbs_to_plot.groupby(by = ['n_pairs']):
#    ax.scatter(grouped.V.squeeze(), grouped.P.squeeze(), label = idx[0], marker = "s")
#ax.legend(title = 'n_pairs')
for idx, row in gibbs_to_plot.iterrows():
    ax.scatter(row.V, np.array(row.P)*1e-5, label = "gibbs "+ str(row.cs[0]), marker = "s")
#fig.savefig("gibbsPV.pdf")

#fig, ax = plt.subplots()
#ax.set_yscale('log')
#ax.set_xscale('log')
#for idx, grouped in gc_to_plot.groupby(by = ['Ncl_eq']):
#    try:
#        ax.scatter(grouped.V.squeeze(), grouped.P.squeeze(), label = idx)
#    except:
#        pass
ax.scatter(gc_to_plot.T.V.squeeze(), gc_to_plot.T.P.squeeze(), label = "GC " + str(gc_to_plot.T.cs.squeeze()))
ax.set_ylim((-1,5))
ax.axhline(y =0, color = "black")
ax.legend(title = 'cs')
fig.savefig("gcPV.pdf")
# %%
