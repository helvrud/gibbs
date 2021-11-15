#%%
import pickle
import pandas as pd
import pathlib
import numpy as np
from mcmd_polyelctrolyte import analytic_donnan

LAST_USED_COLOR = lambda: plt.gca().lines[-1].get_color()

path = pathlib.Path('data/no_diamond_conc_as_arg')
json_files = path.glob('*.pkl')

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
    with open(file, 'rb') as f:
        dicts.append(flatten_dict(pickle.loads(f.read())))


# %%
df = pd.DataFrame(dicts)
df=df.fillna(False)
mean_columns = ['zeta']
df['zeta_mean'] = df['zeta'].apply(np.mean)
df['zeta_err'] = df['zeta'].apply(lambda x: np.std(x)/np.sqrt(len(x)))
# %%
import numpy as np
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
vv = np.linspace(0.2, 0.8)
lvl0 = ['input_c_s_mol', 'input_fixed_anions', 'input_gel_initial_volume']
for idx, grouped in df.groupby(by = lvl0):
    c_s = idx[0]
    n_pairs = 33
    a_fix = idx[1]
    volume_all = idx[2]
    v_ = grouped.input_v
    plt.scatter(v_, grouped.zeta_mean)
    zeta_theory = [analytic_donnan.zeta(n_pairs, a_fix, volume_all*(1-v), volume_all*v) for v in vv]
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
