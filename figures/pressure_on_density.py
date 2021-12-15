#%%
from veusz_embed import *
#%%
import pandas as pd
#%%
df = pd.read_pickle('../data/gel_all_data.pkl')
df.sort_values(by = 'v', inplace = True)
#%%
g =None

df['delta_P_bar_mean'] = df.delta_P_Pa_mean * 1e-5
df['delta_P_bar_err'] = df.delta_P_Pa_err * 1e-5

for (idx, group), color in zip(df.groupby(by = 'n_pairs'), color_cycle):
        g=vplot(
            list(group.gel_density), [list(group.delta_P_bar_mean), list(group.delta_P_bar_err)],
            xname = 'x'+str(idx), yname = 'y'+str(idx),
            g=g, color = color
            )
#%%
g.Save(__file__.replace('.py','.vsz'))
#%%
