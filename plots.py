#%%
import json
import pandas as pd
import pathlib

from donnan_analytic import zeta

path = pathlib.Path('data')
json_files = path.glob('*.json')

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
df['anion_salt'] = df.n_mobile_salt_mean/2
df['anion_gel'] = df.n_pairs - df.anion_salt 
df['zeta'] = df.anion_gel/df.anion_salt*(1-df.v)/df.v
df = df.loc[df['alpha'].isin([0.5])]
#df = df.loc[df['no_gel'] == True]
# %% 
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
vv = np.linspace(0.2, 0.8)
lvl0 = ['alpha', 'n_pairs', 'n_gel', 'system_volume', 'no_interaction']
for idx, grouped in df.groupby(by = lvl0):
    print(idx)
    alpha = idx[0]
    n_pair = np.mean(idx[1])*2
    a_fix = np.mean(grouped.anion_fixed)
    v_ = grouped.v
    plt.scatter(v_, grouped.zeta)
    zeta_theory = [zeta(n_pair, v, a_fix) for v in vv]
    plt.plot(vv, zeta_theory, label = idx)
plt.legend(title=lvl0, bbox_to_anchor=(1.1, 1.05))
plt.arrow(0.3, 0.05, 0.3, 0.0, head_width = 0.02,  transform=ax.transAxes)
plt.text(0.35,0.07, "compression",  transform=ax.transAxes, va='bottom')
plt.text(0.65,0.3, r"$\zeta = \frac{A^{-}_{gel}}{A^{-}_{salt}}$",fontsize=22)
plt.xlabel('v')
plt.ylabel('$\zeta$')
plt.show()

# %%
