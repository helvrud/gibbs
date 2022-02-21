#%%
from cProfile import label
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
pio.renderers.default = "notebook"
#%%
df = pd.read_pickle('../data/gel_all_data.pkl')
df.sort_values(by = 'v', inplace = True)

df = df.loc[df['delta_P_Pa_mean'] < 6e5] #select less than 6bar

df['sample_size'] = df['anion_salt'].apply(len) #get sample size
df = df.loc[df['sample_size'] >30] #select significant samples

#%%
traces = []
for idx, group in df.groupby(by = 'n_pairs'):
    c_s_mol_mean = list(group.c_s_mol_mean)
    c_s_mol_err = list(group.c_s_mol_err)
    gel_density = list(group.gel_density)
    pressure = list(group.delta_P_Pa_mean)
    traces.append(go.Scatter(
        x = gel_density, 
        y = c_s_mol_mean, 
        name = idx, 
        hovertemplate='<br>x:%{x}<br>y:%{y}<br>delta_P:%{text} Pa'))
#%%
fig = go.Figure()
fig.add_traces(traces)

fig.update_layout(
    xaxis = dict(
        type = "log",
        title = "c_gel"
    ),
    yaxis = dict(
        type = "log",
        title = "c_s"
    )
)
# %%
