#%%
from veusz_embed import *
from gc import *
import os
#%%
import pandas as pd
save = True
#%%
df = pd.read_pickle('../data/gel_all_data.pkl')
df.sort_values(by = 'v', inplace = True)

df = df.loc[df['delta_P_Pa_mean'] < 6e5] #select less than 6bar

df['sample_size'] = df['anion_salt'].apply(len) #get sample size
df = df.loc[df['sample_size'] >30] #select significant samples
#%%
g = None




global xy, x_axis, y_axis, x_data, y_data, x_dataname, y_dataname
cs_start = []
cs1 = []
cs2 = []
cs3 = []
cs4 = []
cs5 = []

cs_end = []

for (idx, group), color in zip(df.groupby(by = 'n_pairs'), color_cycle):
    c_s_mol_mean = list(group.c_s_mol_mean)
    c_s_mol_err = list(group.c_s_mol_err)
    gel_density = list(group.gel_density)
    [g, graph, xy]=vplot(
        gel_density, 
        [c_s_mol_mean, c_s_mol_err],
        xname = 'x'+str(idx), yname = 'y'+str(idx),
        xlog = True, ylog = True,
        g=g, color = color
        )
    #xy.key.val = 'c_{s} = '+str(float(group.c_s_reservoir_mol.head(1)))
    xy.key.val = 'c_{{s}} = {:.2e}'.format(float(group.c_s_reservoir_mol.head(1))) 
    cs_start.append(c_s_mol_mean[1])
    cs_end.append(c_s_mol_mean[-1])
    cs1.append(c_s_mol_mean[1])
    cs2.append(c_s_mol_mean[2])
    cs3.append(c_s_mol_mean[3])
    cs4.append(c_s_mol_mean[4])
    cs5.append(c_s_mol_mean[5])
key = graph.Add('key')
key.vertPosn.val = 'top'
key.horzPosn.val = 'left'
key.Border.hide.val  = True
g.Root.page1.graph1.x.label.val = 'hydrogel density, \\varphi, [mol/l]'
g.Root.page1.graph1.y.label.val = 'Salt concentration in hydrogel, [bar]'
#%%



















if save:
    g.Save(__file__.replace('.py','.vsz'))
    fnamevsz = __file__.replace('.py','.vsz')
    fnamepdf = __file__.replace('.py','.pdf')
    g.Save(fnamevsz)
    g.Export(fnamepdf)
    os.popen('veusz '+fnamevsz)
    #%%
