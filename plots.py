#%%
import json
from json.encoder import JSONEncoder
import pandas as pd
import pathlib
import numpy as np

from donnan_analytic import zeta
LAST_USED_COLOR = lambda: plt.gca().lines[-1].get_color()

path = pathlib.Path('data/tests_no_diamond')
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
#arr_columns = ['zeta']
#df = df.apply(lambda x: x.explode() if x.name in arr_columns else x)
mean_columns = ['zeta']
df['zeta_mean'] = df['zeta'].apply(np.mean)
df['zeta_err'] = df['zeta'].apply(lambda x: np.std(x)/np.sqrt(len(x)))
#df['anion_salt'] = df.n_mobile_salt_mean/2
#df['anion_gel'] = df.n_pairs - df.anion_salt 
#df['zeta'] = df.anion_gel/df.anion_salt*(1-df.v)/df.v
#df = df.loc[df['alpha'].isin([0.5, 0.1])]
#df = df.loc[df['no_gel'] == True]
#%%
#path = pathlib.Path('mcmd_polyelctrolyte/monte_carlo/data/')
#json_files = path.glob('*.json')
#
#dicts= []
#for file in json_files:
#    print(file.name)
#    with open(file, 'r') as f:
#        dicts.append(flatten_dict(json.loads(f.read())))
#pure_Donnan = dicts[0]
# %% 
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
n_pairs =100
df = df.loc[df.n_pairs == n_pairs]
fig, ax = plt.subplots()
vv = np.linspace(0.2, 0.8)
lvl0 = ['alpha', 'n_pairs', 'system_volume', 'electrostatic']
for idx, grouped in df.groupby(by = lvl0):
    alpha = idx[0]
    n_pair = n_pairs
    a_fix = int(grouped.anion_fixed.head(1))
    v_ = grouped.v
    plt.scatter(v_, grouped.zeta_mean)
    zeta_theory = [zeta(n_pair, v, a_fix) for v in vv]
    plt.plot(vv, zeta_theory, label = idx)
    plt.errorbar(v_, grouped.zeta_mean, yerr=grouped.zeta_err, linewidth=0, elinewidth=1, color = LAST_USED_COLOR())
plt.legend(title=lvl0, bbox_to_anchor=(1.1, 1.05))
plt.arrow(0.3, 0.05, 0.3, 0.0, head_width = 0.02,  transform=ax.transAxes)
plt.text(0.35,0.07, "compression",  transform=ax.transAxes, va='bottom')
plt.text(0.7,0.1, r"$\zeta = \frac{A^{-}_{gel}}{A^{-}_{salt}}$",fontsize=22, transform=ax.transAxes)
plt.xlabel('v')
plt.ylabel('$\zeta$')
#plt.plot(pure_Donnan['v'], pure_Donnan['zeta'])
plt.show()


# %%

# %%
