def scatter3d(server, client):
    import plotly.express as px
    import pandas as pd
    box_l = server("system.box_l[0]", client).result()
    particles = server("part_data((None,None), {'type':'int','q':'int', 'pos':'list'})", client).result()
    df = pd.DataFrame(particles)
    df.q = df.q.astype('category')
    df[['x', 'y', 'z']] = df.pos.apply(pd.Series).apply(lambda x: x%box_l)
    fig = px.scatter_3d(df, x='x', y='y', z='z', color ='q', symbol = 'type')
    fig.show()

def MCMD(server, MC, step = 0):
    import pandas as pd
    mc_df = pd.DataFrame()
    md_df = pd.DataFrame()
    for k in range(10):
        for i in range(1000):
            mc_df = mc_df.append(
                mc_state_to_df(
                    MC.step(), step
                ), 
                ignore_index=True
            )
            mc_df['note'] = 'equilibration'
            step+=1
        r = server('run_md(200000,20000)',[0,1])
        P_Re = pd.DataFrame(r[1].result()).add_prefix('Re_')
        P_Re['Pressure'] = r[0].result()
        md_df=md_df.append(P_Re, ignore_index=True)
        MC.current_state=MC.setup()
        print(k,i)
        return mc_df, md_df

def mc_state_to_df(state):
    import pandas as pd
    from espresso_nodes.shared import PARTICLE_ATTR
    df = state['particles_info']\
        .groupby(by = ['side', 'type'])\
        .size().unstack(fill_value=0)
    df.columns.name = None
    d = {
        type_:key for key, type_ 
        in zip(PARTICLE_ATTR.keys(),
        [
            ATTR['type'] for ATTR in PARTICLE_ATTR.values()
            ]
        )
    }
    df.rename(columns = d, inplace = True)
    df['energy'] = state['energy']
    df['volume'] = state['volume']
    df = df.reset_index()
    return df

def get_tau(x, acf_n_lags : int = 200):
    from statsmodels.tsa.stattools import acf
    import numpy as np
    acf = acf(x, nlags = acf_n_lags)
    tau_int =1/2+max(np.cumsum(acf))    
    return tau_int

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

def check_if_resampling_required(x, acf_n_lags = 200):
    import numpy as np
    uncorr = ljung_box_white_noise(x)
    if uncorr:
        print('Already not oversampled')
        return 1
    else:
        tau_int =get_tau(x, acf_n_lags)
        if tau_int > 40:
            print(f'Heavily oversampled! Check after resampling')
        print(f'Sample at least {tau_int*2} less often')
        return tau_int*2

def get_min_int_step_recommendation(server, client, proposed_int = 100, sample_size = 5000, acf_n_lags = 200):
    import numpy as np
    observable = server([f'integrate(sample_size = 1, int_steps = {proposed_int})']*sample_size, client).result()
    x = np.array(observable)[:, 0] 
    x = x - np.mean(x)
    tau_int =get_tau(x, acf_n_lags)
    int_recommend = proposed_int*2*tau_int
    #####to be removed##########
    from statsmodels.graphics.tsaplots import plot_acf
    import matplotlib.pyplot as plt
    plot_acf(x, lags = acf_n_lags)
    plt.vlines(x = tau_int*2, ymin = -0.2, ymax = 1)
    plt.show()
    ############################
    return int_recommend

