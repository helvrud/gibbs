#%%
from veusz_embed import *
import os
#%%
import pandas as pd
#%%
df = pd.read_pickle('../data/gel_all_data.pkl')
df.sort_values(by = 'v', inplace = True)

df = df.loc[df['delta_P_Pa_mean'] < 6e5] #select less than 6bar

df['sample_size'] = df['anion_salt'].apply(len) #get sample size
df = df.loc[df['sample_size'] >30] #select significant samples
#%%
g = None




global xy, x_axis, y_axis, x_data, y_data, x_dataname, y_dataname

for (idx, group), color in zip(df.groupby(by = 'n_pairs'), color_cycle):
    [g, graph, xy]=vplot(
        list(group.gel_density), 
        [list(group.c_s_mol_mean), list(group.c_s_mol_err)],
        xname = 'x'+str(idx), yname = 'y'+str(idx),
        xlog = True, ylog = True,
        g=g, color = color
        )
    xy.key.val = 'c_{s} = '+str(float(group.c_s_reservoir_mol.head(1)))


key = graph.Add('key')
key.vertPosn.val = 'top'
key.horzPosn.val = 'left'
key.Border.hide.val  = True
g.Root.page1.graph1.x.label.val = 'hydrogel density, \\varphi, [mol/l]'
g.Root.page1.graph1.y.label.val = 'Salt concentration in hydrogel, [bar]'
#%%


g.Save(__file__.replace('.py','.vsz'))
fnamevsz = __file__.replace('.py','.vsz')
fnamepdf = __file__.replace('.py','.pdf')
g.Save(fnamevsz)
g.Export(fnamepdf)
#os.popen('veusz '+fnamevsz)
#%%
