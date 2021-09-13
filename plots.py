#%%
import json
import pandas as pd
import pathlib

from donnan_analytic import zeta

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
#%%
path = pathlib.Path('data')
json_files = path.glob('*.json')
# %%
dicts= []
for file in json_files:
    print(file.name)
    with open(file, 'r') as f:
        dicts.append(flatten_dict(json.loads(f.read())))
# %%
df = pd.DataFrame(dicts)
# %%
arr_columns = ['n_mobile_salt_eff_sample_size',
       'n_mobile_salt_err', 'n_mobile_salt_mean',
       'pressure_gel_eff_sample_size', 'pressure_gel_err', 'pressure_gel_mean',
       'pressure_salt_eff_sample_size', 'pressure_salt_err',
       'pressure_salt_mean']
#%%
df = df.apply(lambda x: x.explode() if x.name in arr_columns else x)
# %%
DIAMOND_PARTICLES = 248
fixed_anions = df['alpha']*DIAMOND_PARTICLES
mobile_cation_gel = (df['n_mobile'] - df['n_mobile_salt_mean'] - fixed_anions)/2
mobile_cation_salt =  df['n_mobile_salt_mean']/2
df['r'] = mobile_cation_gel/mobile_cation_salt*(1-df['v'])/df['v']
df['r']
df = df.loc[df['alpha']==0.5]
# %% 
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
sns.relplot(data = df, x = 'v', y='r', hue = 'alpha', style = 'n_mobile')
vv = np.linspace(0.2, 0.8)
for idx, grouped in df.groupby(by=['alpha', 'n_mobile']):
    alpha = grouped['alpha'].squeeze()
    n_mobile = grouped['n_mobile'].squeeze()
    a_fix = alpha*DIAMOND_PARTICLES
    zeta_ = [1/zeta(n_mobile, a_fix, v_) for v_ in vv]
    plt.plot(vv, zeta_, label = f'{alpha}_{n_mobile}')
plt.show()
# %%
import seaborn as sns
import matplotlib.pyplot as plt
df['delta_P']=df['pressure_gel_mean']-df['pressure_salt_mean']
sns.relplot(data = df, x = 'v', y='delta_P', hue = 'alpha', style = 'electrostatic')
plt.show()
# %%
