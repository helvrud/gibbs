#%%
import json
from mpmath.functions.functions import im
import pandas as pd
import pathlib

from donnan_analytic import zeta
from mcmd_polyelctrolyte.main import DIAMOND_PARTICLES

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
df=df.fillna(False)
arr_columns = ['n_mobile_salt_eff_sample_size',
       'n_mobile_salt_err', 'n_mobile_salt_mean',
       'pressure_gel_eff_sample_size', 'pressure_gel_err', 'pressure_gel_mean',
       'pressure_salt_eff_sample_size', 'pressure_salt_err',
       'pressure_salt_mean']
df = df.apply(lambda x: x.explode() if x.name in arr_columns else x)
df['anion_fixed'] = df['alpha']*DIAMOND_PARTICLES
anion_salt =  df['n_mobile_salt_mean']/2
anion_gel = (df['n_mobile'] - df['n_mobile_salt_mean'] - df['anion_fixed'])/2
df['zeta'] = anion_gel/anion_salt*(1-df['v'])/df['v']
#df = df.loc[df['alpha'].isin([0, 0.25])]
#df = df.loc[df['no_gel'] == True]
# %% 
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
sns.relplot(data = df, x = 'v', y='zeta', hue = 'no_LJ', style = 'no_gel')
vv = np.linspace(0.2, 0.8)
for idx, grouped in df.groupby(by=['alpha', 'n_mobile']):
    alpha = grouped['alpha'].squeeze()
    no_gel = grouped['no_gel'].squeeze()
    no_LJ = grouped['no_LJ'].squeeze()
    #no_LJ = False
    n_mobile = grouped['n_mobile'].squeeze()
    a_fix = grouped['anion_fixed'].squeeze()
    zeta_ = [zeta(n_mobile-a_fix, v_, a_fix) for v_ in vv]
    plt.plot(vv, zeta_, label = f'{alpha}_{n_mobile}_{no_gel}_{no_LJ}')
plt.arrow(0.3, 0.05, 0.3, 0.0, head_width = 0.02,  transform=ax.transAxes)
plt.text(0.35,0.07, "compression",  transform=ax.transAxes)
plt.text(0.8,0.9, r"$\zeta = \frac{A^{-}_{gel}}{A^{-}_{salt}}$",fontsize=22)
plt.show()

#%%

