# %%
import imp
import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
from scipy.optimize import newton

import plotly.graph_objects as go
import plotly.express as px
import plotly
import plotly.io as pio
pio.renderers.default = "notebook"

from mcmd_polyelctrolyte.utils import n_to_mol

import itertools

def get_color(val, cmin = 0.00, cmax = 0.15):
    from matplotlib import cm
    from matplotlib.colors import ListedColormap, LinearSegmentedColormap

    viridis = cm.get_cmap('brg', 120)
    val = (val-cmin)/(cmax-cmin)
    return viridis(val)


gibbs_data_path = "data/gel_all_data.pkl"
gc_data_path = "data/GC.pkl"
gibbs_raw = pd.read_pickle(gibbs_data_path)
gc_raw = pd.read_pickle(gc_data_path)
# %%
gc = gc_raw
gc["P_err"] = gc_raw.P.apply(lambda _: _[1])
gc.P = gc_raw.P.apply(lambda _: _[0])
gc["gel_density"] = gc.V.apply(lambda x: n_to_mol(480/x))
#%%
#drop wrong ones
gc = gc.loc[~np.isclose(gc.Ncl_eq,440.63)]
gc = gc.loc[~np.isclose(gc.Ncl_eq,1255.399)]
gc.sort_values(by = "cs", inplace = True)
#%%
#interp PV
#%%
#delta_P_polyfit_GC = lambda _, x: np.poly1d(
#    np.polyfit(_.V, _.P, 3)
#    )(x)

#delta_P_polyfit_inv_GC = lambda _, x: np.poly1d(
#    np.polyfit(_.P, _.V, 3)
#    )(x)

#for i in range(0,6):
#    gc[f'V_{i}bar'] = gc.apply(lambda row: delta_P_polyfit_inv_GC(row, i), axis = 1)

#%%
#gc["V_interp"] = gc.apply(lambda row: np.linspace(row.V_0bar, row.V_5bar), axis =1)
#gc["P_interp"] = gc.apply(lambda row: delta_P_polyfit_GC(row, row.V_interp), axis =1)
#%%
fit = lambda x, a, b, c: a*x**2+b*x+c
popt, pcov = curve_fit(fit, np.log(gc.Ncl_eq), np.log(gc.cs))
cs_on_npairs = lambda x: np.exp(fit(np.log(x), *popt))

popt2, pcov2 = curve_fit(fit, np.log(gc.cs), np.log(gc.V_eq))
V_eq_on_cs = lambda x: np.exp(fit(np.log(x), *popt2))

# %%
def PV_GC():
    fig =go.Figure()
    cols = plotly.colors.DEFAULT_PLOTLY_COLORS
    for (i, row), color in zip(gc.iterrows(), cols):
        trace = go.Scatter(
            x = np.array(row.V),
            y = row.P,
            name = '{:.4f}'.format(row.cs)
        )
        fig.add_trace(
            trace
        )
        #x = np.linspace(min(row.V), max(row.V))
        #trace = go.Scatter(
        #    x = row.V_interp,
        #    y = row.P_interp,
        #    name = '{:.4f}'.format(row.cs)
        #)
        #fig.add_trace(
        #    trace
        #)

    fig.update_layout(
        xaxis = dict(
            #type = "log", 
            title = "V_gel [l/mol]", 
            showspikes = True,
            ),
        yaxis = dict(
            title = "pressure [bar]", 
            showspikes = True,
            range=[-0.1,5],
            ),
        legend = dict(title = "c<sub>s</sub><sup>GC</sup>")
    )
    return fig
PV_GC()
#%%
def V_eq_cs():
    fig =go.Figure()
    trace = go.Scatter(
        x = gc.cs,
        y = gc.V_eq,
        mode = "markers",
    )
    fig.add_trace(
        trace
    )
    x = np.geomspace(0.001,1)
    trace = go.Scatter(
            x = x,
            y = V_eq_on_cs(x),
        )
    fig.add_trace(
            trace
        )
    fig.update_layout(
        xaxis = dict(
            type = "log", 
            title = "cs [mol/l]", 
            showspikes = True,
            ),
        yaxis = dict(
            type = "log",
            title = "V_gel [l/mol]", 
            showspikes = True,
            )
    )
    return fig
# %%
def n_pairs_cs():
    fig =go.Figure()
    cols = plotly.colors.DEFAULT_PLOTLY_COLORS
    trace = go.Scatter(
            x = gc.cs,
            y = gc.Ncl_eq,
            mode = "markers",
            showlegend = False
        )
    fig.add_trace(
            trace
        )
    y = np.geomspace(1,600)
    trace = go.Scatter(
            x = cs_on_npairs(y),
            y = y,
        )
    fig.add_trace(
            trace
        )
    fig.update_layout(
        xaxis = dict(
            type = "log", 
            title = "c<sub>s</sub><sup>GC</sup>", 
            showspikes = True,
            ),
        yaxis = dict(
            type = "log",
            title = "Number of pairs in Gibbs Ensemble", 
            showspikes = True,
            )
    )
    return fig
n_pairs_cs()
# %%
#add points from grand canonical
gibbs_raw["c_s_GC"] = gibbs_raw.n_pairs.apply(cs_on_npairs)
gibbs_raw["V_0_GC"] = gibbs_raw.c_s_GC.apply(V_eq_on_cs)
gibbs_raw["c_gel_0_GC"] = gibbs_raw.V_0_GC.apply(lambda x: 1/x)
#select only significant
plot_data = gibbs_raw.loc[gibbs_raw['delta_P_Pa_mean'] < 6e5]
plot_data['sample_size'] = plot_data['anion_salt'].apply(len)
plot_data = plot_data.loc[plot_data['sample_size'] >30]
plot_data['c_s_reservoir_mol'] = plot_data['c_s_reservoir_mol'].astype('category')
plot_data['box_l'] = plot_data['V0']**(1/3)
# %%
#let us add some interpolation
data_pivot = pd.pivot_table(
    plot_data, 
    index =  [
        'n_pairs', 
        'V0', 
        'fixed_anions', 
        'c_s_reservoir_mol', 
        'V_0_GC',
        "c_s_GC",
        "c_gel_0_GC",
        ], 
    values = [
        #'v',
        'gel_density',
        #'zeta_mean', 
        'c_s_mol_mean',
        'delta_P_Pa_mean', 
        ],
    aggfunc = list).reset_index()


c_s_polyfit = lambda _, x : np.exp(
    np.poly1d(
        np.polyfit(np.log(_.gel_density), np.log(_.c_s_mol_mean), 2)
        )(np.log(x))
    )

delta_P_polyfit = lambda _, x: np.poly1d(
    np.polyfit(_.gel_density, _.delta_P_Pa_mean, 2)
    )(x)

delta_P_polyfit_inv = lambda _, x: np.poly1d(
    np.polyfit(_.delta_P_Pa_mean, _.gel_density, 2)
    )(x)

#%%
for i in range(0,6):
    data_pivot[f'c_gel_{i}bar'] = data_pivot.apply(lambda row: delta_P_polyfit_inv(row, i*1e5), axis = 1)
    data_pivot[f'c_s_{i}bar'] = data_pivot.apply(lambda row: c_s_polyfit(row, row[f'c_gel_{i}bar']), axis = 1)
#%%
data_pivot["c_gel_interp"] = data_pivot.apply(lambda row: np.linspace(row.c_gel_0_GC, row.c_gel_5bar), axis =1)
data_pivot["c_s_interp"] = data_pivot.apply(lambda row: c_s_polyfit(row, row.c_gel_interp), axis =1)
data_pivot["delta_P_interp"] = data_pivot.apply(lambda row: delta_P_polyfit(row, row.c_gel_interp)*1e-5, axis =1)
# %%
fig =go.Figure()
cols = plotly.colors.DEFAULT_PLOTLY_COLORS
for i, row in data_pivot.iterrows():
    color = f'rgba{get_color(row.c_s_GC)}'
    trace_c_s = go.Scatter(
        x = row.gel_density,
        y = row.c_s_mol_mean,
        mode = "markers",
        marker = dict(color = color, size =3),
        showlegend = False,
        text=np.array(row.delta_P_Pa_mean)*1e-5,
        hovertemplate='<br>c_gel:%{x}<br>c_s:%{y}<br>delta_P:%{text} bar'

    )
    fig.add_trace(
        trace_c_s
    )

    trace_GC = go.Scatter(
        x = [row.c_gel_0_GC],
        y = [row.c_s_GC],
        mode = "markers",
        line = dict(color = color),
        #name = row.n_pairs,
        showlegend = False
    )
    fig.add_trace(
        trace_GC
    )
    
    trace_c_s_poly = go.Scatter(
        x = row.c_gel_interp,
        y = row.c_s_interp,
        mode = "lines",
        line = dict(color = color),
        name = '{:.4f}'.format(row.c_s_GC),
        text=np.array(row.delta_P_interp),
        hovertemplate='<br>c_gel:%{x}<br>c_s:%{y}<br>delta_P:%{text} bar'
    )
    fig.add_trace(
        trace_c_s_poly
    )

for i, row in gc.iterrows():
    color = f'rgba{get_color(row.cs)}'
    trace = go.Scatter(
        x = 1/np.array(row.V),
        y = [row.cs]*len(row.V),
        name = '{:.4f}'.format(row.cs)+ "(GC)",
        line = dict(color = color, width = 1),
        text = row.P,
        hovertemplate='<br>c_gel:%{x}<br>c_s:%{y}<br>delta_P:%{text} bar'
    )
    fig.add_trace(
        trace
    )

for i in range(0,6):
    trace = go.Scatter(
        x = data_pivot[f'c_gel_{i}bar'],
        y = data_pivot[f'c_s_{i}bar'],
        line = dict(color = "lightgrey"),
        text=data_pivot.c_s_GC,
        hovertemplate='c_s_GC:%{text} mol/l',
        showlegend = False,
    )
    fig.add_trace(
        trace
    )

fig.update_layout(
    xaxis = dict(
        type = "log", 
        title = "c<sub>gel</sub> [mol/l]",
        range = [-1,0.2],
        showgrid = False,
        ),
    yaxis = dict(
        type = "log", 
        title = "c<sub>s</sub> [mol/l]",
        showgrid = False,
        ),
    legend = dict(
        title = "c<sub>s</sub><sup>GC</sup>"
        )
)
fig.show("browser")
# %%
fig =go.Figure()
cols = plotly.colors.DEFAULT_PLOTLY_COLORS
for i, row in data_pivot.iterrows():
    color = f'rgba{get_color(row.c_s_GC)}'
    trace_P = go.Scatter(
        x = 1/np.array(row.gel_density),
        y = np.array(row.delta_P_Pa_mean)*1e-5,
        mode = "markers",
        marker = dict(color = color, size =3),
        showlegend = False,
        #text=row.c_s_mol_mean,
        #hovertemplate='<br>V_gel:%{x} mol/l<br>delta_P:%{y} bar<br>c_s:%{text} mol/l',
        hoverinfo='none'
    )
    #fig.add_trace(
    #    trace_P
    #)

    x=np.linspace(row.c_gel_0_GC, row.c_gel_5bar)
    y = delta_P_polyfit(row,x)*1e-5
    
    #y = np.linspace(0,6)
    #x = delta_P_polyfit_inv(row,y*1e5)
    
    trace_P_poly = go.Scatter(
        x = 1/x,
        y = y,
        mode = "lines",
        line = dict(color = color),
        name = '{:.4f}'.format(row.c_s_GC),
        text=row.c_s_mol_mean,
        hovertemplate='<br>V_gel:%{x} mol/l<br>delta_P:%{y} bar<br>c_s:%{text} mol/l'
    )
    fig.add_trace(
        trace_P_poly
    )
for i, row in gc.iterrows():
    color = f'rgba{get_color(row.cs)}'
    trace = go.Scatter(
        x = np.array(row.V),
        y = row.P,
        name = '{:.4f}'.format(row.cs)+ "(GC)",
        line = dict(color = color, dash = "dash")
    )
    fig.add_trace(
        trace
    )
fig.update_layout(
    xaxis = dict(
        #type = "log", 
        title = "V_gel [l/mol]", 
        showspikes = True,
        range = [0.6, 10],
        #grid = False,
        ),
    yaxis = dict(
        #type = "log",
        title = "pressure [bar]", 
        showspikes = True,
        range = [0,5],
        #grid = False,
        ),
    legend = dict(title = "c<sub>s</sub><sup>GC</sup>")
)
# %%

# %%
#I have found that we need
#c_s about 0.074
#c_gel about 0.2500
c_s = 0.074
c_gel = 0.24
#c_s = 0.074 coresponds to n_pairs 86
#-->
n_pairs = 86
box_l = 42

#%%
from mcmd_polyelctrolyte.utils import mol_to_n
volume = mol_to_n(488/c_gel)*1000
volume**(1/3)
# %%
