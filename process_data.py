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

