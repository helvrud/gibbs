#%%
import numpy as np
import pickle
from numpy.core.fromnumeric import mean
import pandas as pd
import pathlib



def flatten_dict(d, prefix='_'):
    def items():
        # A clojure for recursively extracting dict like values
        for key, value in d.items():
            if isinstance(value, dict):
                for sub_key, sub_value in flatten_dict(value).items():
                    # Key name should imply nested origin of the dict,
                    # so we use a default prefix of __ instead of _ or .
                    yield key + prefix + sub_key, sub_value
            else:
                yield key, value
    return dict(items())

def read_data(path, cast_pandas = True):
    pkl_files = path.glob('*.pkl')
    dicts= []
    for file in pkl_files:
        print(file.name)
        with open(file, 'rb') as f:
            dicts.append(flatten_dict(pickle.loads(f.read())))
    if cast_pandas:
        return pd.DataFrame(dicts)
    else:
        return dicts

def mean_and_err(column_name, df):
    if isinstance(df[column_name][0], np.ndarray):
        try:
            df[column_name +"_mean"] = df[column_name].apply(np.mean)
            df[column_name +"_err"]=df[column_name].apply(lambda _: np.std(_)/np.sqrt(len(_)))
        except:
            pass

def split_2d_arrays_in_columns(column_name, df, postfix = None, replace = True):
    if postfix is None:
        indices = range(np.shape(df[column_name][0])[1])
        for i in indices:
            df[column_name+'_'+f'{i}'] = df[column_name].apply(lambda _: _[:,i])
    else:
        for i, pst in enumerate(postfix):
            df[column_name+'_'+pst] = df[column_name].apply(lambda _: _[:,i])
    if replace:
        del df[column_name]



#%%
path = pathlib.Path('data/diamond_n_pairs')
pickle_path = pathlib.Path('data/gel_all_data.pkl')
df = read_data(path)

columns_to_store =[
    'anion', 'cation', 'zeta', 'pressure',
    'input_gel_initial_volume', 'input_n_pairs_all', 'input_fixed_anions',
    'input_v', 'input_MPC', 'input_electrostatic'
]

df = df[columns_to_store]

salt_gel_columns = ['anion', 'cation', 'pressure']

for col in salt_gel_columns: df[col] = df[col].apply(np.array)

columns_to_rename = {
    'input_gel_initial_volume' : 'V0', 
    'input_n_pairs_all' : 'n_pairs', 
    'input_fixed_anions' : 'fixed_anions',
    'input_v' : 'v', 
    'input_MPC' : 'MPC', 
    'input_electrostatic' : 'electrostatic', 
}

df.rename(columns = columns_to_rename, inplace=True)

n_pairs_c_s_mol = {
    229 : 0.2083,
    138 : 0.1308,
    71 : 0.0617,
    11 : 0.0111,
    5 : 0.0065
}
def f(x):
    if x in n_pairs_c_s_mol: return n_pairs_c_s_mol[x]
    else: return None
df['c_s_reservoir_mol'] = df.n_pairs.apply(f)
#%%
# %%
for col in salt_gel_columns:
    try:
        split_2d_arrays_in_columns(col, df, postfix=['salt', 'gel'])
    except Exception as e:
        print(e)
#%%
from mcmd_polyelctrolyte.utils import n_to_mol
df['volume_gel'] = df.v*df.V0
df['volume_salt'] = (1-df.v)*df.V0
df['c_s_mol'] = df.apply(lambda _: n_to_mol(_.anion_salt/_.volume_salt), axis =1)
df['gel_density'] = df.apply(lambda _: n_to_mol((_.MPC*16+8)/_.volume_salt), axis =1)
#%%
for col in df.columns:
    try:
        mean_and_err(col, df)
    except:
        pass
#%%
df.to_pickle(pickle_path)
df.to_hdf('data.hdf', key = 'diamond')
# %%
import seaborn as sns
import matplotlib.pyplot as plt
#%%
df.n_pairs=df.n_pairs.astype('category')
df.c_s_reservoir_mol=df.c_s_reservoir_mol.astype('category')
sns.scatterplot(data = df, x = 'gel_density', y = 'c_s_mol_mean', hue = 'c_s_reservoir_mol', style = 'n_pairs')
plt.xscale('log')
plt.yscale('log')
# %%
g =None
for idx, group in df.groupby(by = 'n_pairs'):
        g=vplot(
            list(group.gel_density), list(group.c_s_mol_mean),
            xname = 'x'+str(idx), yname = 'y'+str(idx),
            g=g
            )
#%%
import veusz.embed as veusz
def addxy(graph,
        x_dataname='',
        y_dataname='',
        marker='circle', markersize='2pt', color = 'black', style = 'dotted',
        keylabel = '',
        xname='', yname='',
        xlog=False, ylog=False):
    # adds an xy plot to a graph
    global xy
    xy = graph.Add('xy')

    xy.xData.val = x_dataname
    xy.yData.val = y_dataname
    xy.marker.val = marker
    xy.MarkerFill.color.val = color
    xy.MarkerLine.color.val = 'transparent'

    xy.markerSize.val = markersize

    xy.PlotLine.width.val = '2pt'
    xy.PlotLine.style.val = style
    xy.PlotLine.color.val = color
    xy.ErrorBarLine.color.val = color
    # ~ xy.PlotLine.hide.val = not PlotLine


    keylabels = []
    for i in graph.childnames:
        if i[:2] == 'xy':
            exec('keylabels.append(graph.'+i+'.key.val)')

    if not keylabel in keylabels: xy.key.val = keylabel
    x_axis = graph.x
    y_axis = graph.y
    x_axis.label.val = xname
    x_axis.log.val = xlog
    y_axis.label.val = yname
    y_axis.log.val = ylog

    #~ y_axis.min.val = -1.1
    #~ y_axis.max.val = 1.1

    #~ x_axis.min.val = 0.25
    #~ x_axis.max.val = 0.6

    xy.ErrorBarLine.width.val = '2pt'

def vplot(  x=[],y=[],
            xname = 'x', yname = 'y',
            xlog = False, ylog = False,
            color = 'black',
            style='dotted', PlotLine = True, marker = 'circle', markersize = '2pt', keylabel='', title='notitle',
            g = None, graph=None  ):

    global xy, x_axis, y_axis, x_data, y_data, x_dataname, y_dataname
    figsize = 16
    aspect = 1.6
    if x == []:
        x = range(len(y))


    if g == None:
        g = veusz.Embedded(title)
        g.EnableToolbar()
        page = g.Root.Add('page')
        graph = page.Add('graph')
    else:
        if type(graph) != veusz.WidgetNode:
            page = g.Root.page1
            graph = page.graph1
        else:
            print(graph)
            print()
            print()
            print()
            print()
    page.width.val = str(figsize)+'cm'
    page.height.val = str(figsize / aspect)+'cm'


    x_dataname  = xname
    y_dataname  = yname

    if len(np.shape(x)) == 2:
        x_data = x[0]
        x_data_err = x[1]
        g.SetData(x_dataname, x_data, symerr = x_data_err)
    else:
        x_data = x
        g.SetData(x_dataname, x_data)
    if len(np.shape(y)) == 2:
        y_data = y[0]
        y_data_err = y[1]
        g.SetData(y_dataname, y_data, symerr = y_data_err)
    else:
        y_data = y
        g.SetData(y_dataname, y_data)



    addxy(graph, x_dataname = x_dataname, y_dataname = y_dataname, marker=marker, markersize=markersize, color=color, style = style, keylabel = keylabel, xname=xname, yname=yname, xlog=xlog, ylog=ylog)
    if len(x_data) == 1:
        xy.MarkerLine.color.val = xy.MarkerFill.color.val;xy.MarkerFill.color.val = 'white'; xy.MarkerLine.width.val = '1.0pt'
    #~ xy_sim.ErrorBarLine.transparency.val = 50


    return g 

# %%
