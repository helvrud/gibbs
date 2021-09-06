def get_tau(x, acf_n_lags : int = 200):
    #Janke, Statistical analysis of simulations: Data correlations and error
    #estimation, Quantum Simulations of Complex Many-Body Systems: From
    #Theory to Algorithms, Lecture Notes, NIC, Jülich, 2002, 10, 423–445,
    #https://www.physik.uni-leipzig.de/~janke/Paper/nic10_423_2002.pdf
    #eq. 24
    from statsmodels.tsa.stattools import acf
    import numpy as np
    acf = acf(x, nlags = acf_n_lags)
    tau_int =1/2+max(np.cumsum(acf))    
    return tau_int

def correlated_data_mean_err(x, tau, ci = 0.95):
    import scipy.stats
    import numpy as np
    x_mean = np.mean(x)
    n_eff = np.size(x)/(2*tau)
    print(f"Effective sample size: {n_eff}")
    #add reference
    t_value=scipy.stats.t.ppf(1-(1-ci)/2, n_eff)
    print(f"t-value: {t_value}")
    err = np.std(x)/np.sqrt(n_eff) * t_value
    return x_mean, err



