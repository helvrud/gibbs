#%%
def ljung_box_white_noise(x):
    from statsmodels.tsa.stattools import acf
    from statsmodels.stats.diagnostic import acorr_ljungbox
    from scipy.stats import chi2
    p= acorr_ljungbox(acf(x), lags=[40])[1][0]
    passed = p>0.05
    if passed:
        print('Test passed')
    else:
        print('Test failed')
    print(p)
    return passed

def downsample(x, dist):
    import random
    import numpy as np
    n_chunks = int(len(x)/dist)
    return [random.choice(chunk) for chunk in np.array_split(x,n_chunks)]

def check_stationarity(x, p_crit=0.05):
    from statsmodels.tsa.stattools import adfuller
    p = adfuller(x)[1]
    passed = p<p_crit
    if passed:
        print('Reject H0, the data is stationary.')
    else:
        print('Failed to reject H0, the data is not stationary.')
    return passed

def zeta_analytic(N_pairs, A_fix, v):
    """Returns zeta = anion_gel/anion_salt

    Args:
        N_pairs (float): total number of mobile ion pairs
        A_fix (float): number of fixed anions
        v (float): gel relative volume

    Returns:
        [float]: relative anion_gel/anion_salt
    """
    if v == 0.5:
        zeta = (A_fix + N_pairs**2/(A_fix + 2*N_pairs))/(-N_pairs**2/(A_fix + 2*N_pairs) + N_pairs)
    else:
        import numpy as np
        sqrt = np.sqrt
        zeta = (1 - v)*(A_fix + (A_fix*(1 - v)**2/2 + N_pairs*v**2 - (1 - v)*sqrt(A_fix**2*(1 - v)**2 + 4*A_fix*N_pairs*v**2 + 4*N_pairs**2*v**2)/2)/(v**2 - (1 - v)**2))/(v*(N_pairs - (A_fix*(1 - v)**2/2 + N_pairs*v**2 - (1 - v)*sqrt(A_fix**2*(1 - v)**2 + 4*A_fix*N_pairs*v**2 + 4*N_pairs**2*v**2)/2)/(v**2 - (1 - v)**2)))
    return zeta

def mol_to_n(mol_conc, unit_length_nm=0.35):
    #Navogadro = 6.02214e23
    #1e-9**3 * 10**3 = 10e-24
    #6.022e23*10e-24 = 6.022e-1
    n = unit_length_nm**3*6.02214e-1*mol_conc
    return n

def n_to_mol(n, unit_length_nm=0.35):
    #Navogadro = 6.02214e23
    #1e-9**3 * 10**3 = 10e-24
    #6.022e23*10e-24 = 6.022e-1
    mol_conc = n/(unit_length_nm**3*6.02214e-1)
    return mol_conc

def pressure_to_Pa(pressure_kT, unit_length_nm=0.35):
    #kT = 1.38064852*300*e-23
    #vol_unit = sigma^3 *1e-27
    pressure = pressure_kT*(300*1.38064852/unit_length_nm**3)*10**4
    return pressure


def sample_all(
        MC, sample_size, timeout,
        n_particle_sampling_kwargs = None, pressure_sampling_kwargs = None):
    try:
        from tqdm import trange
    except:
        trange = range
    import numpy as np
    import time
    start_time = time.time()

    results_ld = [] #list of dicts

    for i in trange(sample_size):
        if time.time()-start_time > timeout:
            print("Timeout is reached, return already calculated data")
            break
        try:
            n_particles_sample = MC.sample_particle_count_to_target_error(
                **n_particle_sampling_kwargs
            )
        except Exception as e:
            print('An error occurred, return already calculated data')
            print(e)
            break

        #probably we can dry run some MD without collecting any data
        try:
            pressures_sample = MC.sample_pressures_to_target_error(
                **pressure_sampling_kwargs
                )
        except Exception as e:
            print('An error occurred, return already calculated data')
            print(e)
            break

        #discard info about errors
        del n_particles_sample['err']
        del n_particles_sample['sample_size']
        del pressures_sample['err']
        del pressures_sample['sample_size']

        res_dict = {**n_particles_sample, **pressures_sample}
        results_ld.append(res_dict)

    #convert list of dicts to dict of lists
    results_dl = {k: [dic[k] for dic in results_ld] for k in results_ld[0]}
    results_dl = {k: np.array(v) for k,v in results_dl.items()}
    print('Sampling done, returning the data')
    return results_dl


def plotly_scatter3d(server, client):
    import plotly.express as px
    import pandas as pd
    box_l = server("system.box_l[0]", client).result()
    particles = server("part_data((None,None), {'type':'int','q':'int', 'pos':'list'})", client).result()
    df = pd.DataFrame(particles)
    df.q = df.q.astype('category')
    df[['x', 'y', 'z']] = df.pos.apply(pd.Series).apply(lambda x: x%box_l)
    fig = px.scatter_3d(df, x='x', y='y', z='z', color ='q', symbol = 'type')
    fig.show()