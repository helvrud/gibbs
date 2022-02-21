#%%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import functools
#matplotlib settings
LAST_USED_COLOR = lambda: plt.gca().lines[-1].get_color()
plt.rcParams['axes.xmargin'] = 0
plt.rcParams['axes.ymargin'] = 0
import scipy.optimize

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
gibbs_raw.sort_values
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
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
pio.renderers.default = "notebook"
#%%
fig = go.Figure()
fig.add_trace(trace_P_c)
# %%
def fit_function(c_s, c_gel, x):
    return x[0]*c_gel + x[1]*c_gel**2 + x[2]*c_s + x[3]*c_s**2

def solve(fit_func, delta_P, x0, **kwargs):
    def cost_func(x):
        f = np.vectorize(functools.partial(fit_func, x=x))
        resids = delta_P - f(**kwargs)
        return resids
    return scipy.optimize.least_squares(cost_func, x0=x0, method = 'lm')

#%%
x0 = np.random.random_sample(size=4)
c_s = gibbs_raw.c_s_mol_mean.to_numpy()
c_gel = gibbs_raw.c_gel.to_numpy()
c_s_reservoir = gibbs_raw.c_s_reservoir_mol.to_numpy()
delta_P = gibbs_raw.delta_P_Pa_mean.to_numpy()
# %%
#lm = solve(fit_function, c_s, c_gel, delta_P, x0)
lm = solve(
    fit_function, 
    delta_P, 
    x0=np.random.random_sample(size=4), 
    c_s=c_s, 
    c_gel = c_gel
    )
fit = np.vectorize(functools.partial(fit_function, x = lm.x))
c_s_=np.linspace(min(c_s), max(c_s))
c_gel_=np.linspace(min(c_gel), max(c_gel))
delta_P_ = fit(*np.meshgrid(c_s_, c_gel_))
#%%
trace_P_c_model = go.Surface(
    x = c_gel_,
    y = c_s_,
    z = delta_P_.T,
    opacity = 0.5
    )
trace_P_c = go.Scatter3d(
    x = gibbs_raw.c_gel, 
    y = gibbs_raw.c_s_mol_mean,
    z = gibbs_raw.delta_P_Pa_mean,
    marker=dict(color = gibbs_raw.delta_P_Pa_mean),
    mode='markers',
    )
#%%
fig = go.Figure()
fig.add_traces([
    trace_P_c_model, 
    trace_P_c])

fig.update_layout(
    scene = dict(
        xaxis = dict(title = "c_gel [mol/l]"),
        zaxis = dict(title = "delta_P [bar]"),
        yaxis = dict(title = "c_s [mol/l]"),
    )
)
# %%
trace_P_c_model = go.Surface(
    x = c_gel_,
    y = c_s_,
    z = delta_P_.T,
    opacity = 0.5
    )
trace_P_c = go.Scatter3d(
    x = gibbs_raw.c_gel, 
    y = gibbs_raw.c_s_mol_mean,
    z = gibbs_raw.delta_P_Pa_mean,
    marker=dict(color = gibbs_raw.delta_P_Pa_mean),
    mode='markers',
    )
#%%
fig = go.Figure()
fig.add_traces([
    trace_P_c_model, 
    trace_P_c])

fig.update_layout(
    scene = dict(
        xaxis = dict(title = "c_gel [mol/l]"),
        zaxis = dict(title = "delta_P [bar]"),
        yaxis = dict(title = "c_s [mol/l]"),
    )
)