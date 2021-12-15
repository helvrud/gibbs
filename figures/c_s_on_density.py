#%%
from veusz_embed import *
#%%
import pandas as pd
#%%
df = pd.read_pickle('../data/gel_all_data.pkl')
df.sort_values(by = 'v', inplace = True)
#%%
g =None
page = None
for (idx, group), color in zip(df.groupby(by = 'n_pairs'), color_cycle):
        g=vplot(
            list(group.gel_density), np.array([list(group.c_s_mol_mean), list(group.c_s_mol_err)]),
            xname = 'x'+str(idx), yname = 'y'+str(idx),
            g=g, color = color, xlog = True, ylog = True
            )
#%%
g.Save(__file__.replace('.py','.vsz'))
#%%