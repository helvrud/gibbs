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
global xy, x_axis, y_axis, x_data, y_data, x_dataname, y_dataname
for (idx, group), color in zip(df.groupby(by = 'n_pairs'), color_cycle):
    [g, graph, xy]=vplot(
        list(group.gel_density), [list(group.delta_P_bar_mean), list(group.delta_P_bar_err)],
        xname = 'x'+str(idx), yname = 'y'+str(idx), xlog = True,
        g=g, color = color
        )
    xy.key.val = 'c_{s} = '+str(float(group.c_s_reservoir_mol.head(1)))
graph.y.max.val=5
graph.y.min.val=0
key = graph.Add('key')
key.vertPosn.val = 'top'
key.horzPosn.val = 'left'
key.Border.hide.val  = True
g.Root.page1.graph1.x.label.val = 'hydrogel density, \\varphi, [mol/l]'
g.Root.page1.graph1.y.label.val = '\\Delta P = P - P_{res}, [bar]'

#%%
g.Save(__file__.replace('.py','.vsz'))
#%%
