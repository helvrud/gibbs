#%%
from veusz_embed import *
#%%
import pandas as pd
#%%
df = pd.read_pickle('../data/gel_all_data.pkl')
df.sort_values(by = 'v', inplace = True)
#%%
g =None
for (idx, group), color in zip(df.groupby(by = 'n_pairs'), color_cycle):
        g=vplot(
            list(group.gel_density), [list(group.pressure_gel_mean - group.pressure_salt_mean), list(group.pressure_gel_err + group.pressure_salt_err)],
            xname = 'x'+str(idx), yname = 'y'+str(idx),
            g=g, color = color
            )
#%%
g.Save(__file__.replace('.py','.vsz'))
#%%