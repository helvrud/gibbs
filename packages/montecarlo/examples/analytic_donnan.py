import numpy as np

def gel_anions(n_pairs, fixed_anions, v_salt, v_gel):
    if v_salt == v_gel:
        n_anions = n_pairs**2/(fixed_anions + 2*n_pairs)
    else:
        #found with sympy
        n_anions = (
            fixed_anions*v_salt**2/2
            + n_pairs*v_gel**2
            - v_salt*np.sqrt(
                fixed_anions**2*v_salt**2
                + 4*fixed_anions*n_pairs*v_gel**2
                + 4*n_pairs**2*v_gel**2
            )/2)/(v_gel**2 - v_salt**2)
    return n_anions

def gel_anions_inf_reservoir(c_s, fixed_anions, v_gel):
    n_anions = np.sqrt(fixed_anions**2 + 4*c_s**2*v_gel**2)/2 - fixed_anions/2
    return n_anions

def speciation(n_pairs, fixed_anions, v_salt, v_gel):
    anion_gel = gel_anions(n_pairs, fixed_anions, v_salt, v_gel)
    cation_gel = anion_gel+fixed_anions
    anion_salt = cation_salt = n_pairs-anion_gel
    return anion_salt, anion_gel, cation_salt, cation_gel

def speciation_inf_reservoir(c_s, fixed_anions, v_gel):
    anion_gel = gel_anions_inf_reservoir(c_s, fixed_anions, v_gel)
    cation_gel = anion_gel+fixed_anions
    return anion_gel, cation_gel

def speciation_compressed(c_s, fixed_anions, gel_initial_volume, v):
    anion_gel_inf, cation_gel_inf = speciation_inf_reservoir(c_s, fixed_anions, gel_initial_volume)
    gel_volume = gel_initial_volume*v
    salt_volume = gel_initial_volume*(1-v)
    return speciation(anion_gel_inf, fixed_anions, salt_volume, gel_volume)

def zeta(n_pairs, fixed_anions, v_salt, v_gel):
    anion_salt, anion_gel, cation_salt, cation_gel = speciation(n_pairs, fixed_anions, v_salt, v_gel)
    zeta = anion_gel*v_salt/(anion_salt*v_gel)
    return zeta

def zeta_compressed(c_s, fixed_anions, gel_initial_volume, v):
    anion_salt, anion_gel, cation_salt, cation_gel = speciation_compressed(c_s, fixed_anions, gel_initial_volume, v)
    zeta = anion_gel*(1-v)/(anion_salt*v)
    return zeta