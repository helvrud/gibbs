#%%
import numpy as np

def gel_cations(n_pairs, fixed_anions, v_salt, v_gel):
    if v_salt==v_gel:
        n_cations = n_pairs**2/(fixed_anions + 2*n_pairs)
    else:
        n_cations = (
            fixed_anions*v_salt**2/2 \
            + n_pairs*v_gel**2 \
            - v_salt*np.sqrt(
                fixed_anions**2*v_salt**2 \
                + 4*fixed_anions*n_pairs*v_gel**2 \
                + 4*n_pairs**2*v_gel**2
            )/2)/(v_gel**2 - v_salt**2)
    return n_cations

def gel_cations_inf_reservoir(c_s, fixed_anions, v_gel):
    n_cations = np.sqrt(fixed_anions**2 + 4*c_s**2*v_gel**2)/2 - fixed_anions/2
    return n_cations

def speciation(n_pairs, fixed_anions, v_salt, v_gel):
    cation_gel = gel_cations(n_pairs, fixed_anions, v_salt, v_gel)
    anion_gel = cation_gel+fixed_anions
    anion_salt = cation_salt = n_pairs-cation_gel
    return anion_salt, anion_gel, cation_salt, cation_gel

def speciation_inf_reservoir(c_s, fixed_anions, v_gel):
    cation_gel = gel_cations_inf_reservoir(c_s, fixed_anions, v_gel)
    anion_gel = cation_gel+fixed_anions
    return anion_gel, cation_gel
# %%
