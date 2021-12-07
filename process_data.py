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
df = read_data(path)
# %%
for col in df.columns:
    print(col)
    try:
        split_2d_arrays_in_columns(col, df, postfix=['salt', 'gel'])
    except:
        pass
#%%
for col in df.columns:
    print(col)
    try:
        mean_and_err(col, df)
    except:
        pass
# %%
