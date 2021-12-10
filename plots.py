#%%
import pickle
import pandas as pd
import pathlib
import numpy as np
from mcmd_polyelctrolyte import analytic_donnan
from mcmd_polyelctrolyte import utils

LAST_USED_COLOR = lambda: plt.gca().lines[-1].get_color()

path = pathlib.Path('data/diamond_n_pairs')
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

df['pressure_0_mean']=df['pressure'].apply(lambda _: np.mean(_, axis=0)[0])
df['pressure_1_mean']=df['pressure'].apply(lambda _: np.mean(_, axis=0)[1])

df['anion_salt_mean']=df['anion'].apply(lambda _: np.mean(_, axis=0)[0])
df['anion_salt_conc']=df.anion_salt_mean/(df.input_gel_initial_volume*(1-df.input_v))
df['anion_salt_conc_mol'] = df['anion_salt_conc'].apply(utils.n_to_mol)

df['pressure_0_err']=df['pressure'].apply(lambda _: np.std(_, axis=0)[0]/np.sqrt(len(_)))
df['pressure_1_err']=df['pressure'].apply(lambda _: np.std(_, axis=0)[1]/np.sqrt(len(_)))
#df = df.loc[df['sample_size']==200]

n_particles = df['anion'].apply(lambda _: np.mean(_, axis =0)).apply(sum) +\
    df['cation'].apply(lambda _: np.mean(_, axis =0)).apply(sum)
df['n_pairs'] = round((n_particles - df['input_fixed_anions'])/2,3)

# %%
import numpy as np
import matplotlib.pyplot as plt
fig, (ax, ax2, ax3) = plt.subplots(nrows=3, sharex=True)
vv = np.linspace(0.2, 0.9)
lvl0 = ['input_n_pairs_all', 'input_fixed_anions', 'input_gel_initial_volume', 'input_electrostatic']
for idx, grouped in df.groupby(by = lvl0):
    c_s = idx[0]
    n_pairs = grouped.n_pairs.mean()
    a_fix = idx[1]
    volume_all = idx[2]
    v_ = grouped.input_v
    #ax.scatter(v_, grouped.zeta_mean)
    #zeta_theory = [analytic_donnan.zeta(n_pairs, a_fix, volume_all*(1-v), volume_all*v) for v in vv]
    #zeta_theory = [analytic_donnan.zeta_compressed(utils.mol_to_n(c_s), a_fix, volume_all, v) for v in vv]
    ax.errorbar(v_, grouped.zeta_mean, yerr=grouped.zeta_err, linewidth=0, elinewidth=1, marker = 'o', ms=2)
    #ax.plot(vv, zeta_theory, color = ax.lines[-1].get_color())
    p = utils.pressure_to_Pa(grouped.pressure_1_mean-grouped.pressure_0_mean)
    p_err = utils.pressure_to_Pa(grouped.pressure_1_err-grouped.pressure_0_err)
    ax2.errorbar(
        v_, p*1e-5, yerr = p_err*1e-5,
        color = ax.lines[-1].get_color(),
        linewidth=0, elinewidth=1, marker = 'o', ms=2,
        label = (idx[0], idx[1], idx[2], idx[3])
        )
    ax3.scatter(
        v_, grouped.anion_salt_conc_mol,
        color = ax.lines[-1].get_color(),
    )
    ax3.set_yscale('log')

    #ax2.errorbar(v_, grouped.pressure_0_mean, yerr = grouped.pressure_0_err, linewidth=0, elinewidth=1, marker = 's', color = 'red')
    #ax2.errorbar(v_, grouped.pressure_1_mean, yerr = grouped.pressure_1_err, linewidth=0, elinewidth=1, color = 'green')


ax2.legend(title="ion_pairs_mobile, anion_fixed, volume_all, electrostatic")
plt.text(0.5,0.93, "← compression",  transform=ax.transAxes, va='bottom')
plt.text(0.7,0.1, r"$\zeta = \frac{A^{-}_{gel}}{A^{-}_{salt}}$",fontsize=22, transform=ax.transAxes)
plt.xlabel('v')
ax.set_ylabel('$\zeta$')
ax2.set_ylabel('$pressure$, bar')
ax3.set_ylabel('$\log(A_{salt}^{-})$')
#ax3.set_ylabel('$A_{salt}^{-}$')
#plt.plot(pure_Donnan['v'], pure_Donnan['zeta'])
fig.set_size_inches(7,9)
plt.show()
# %%
