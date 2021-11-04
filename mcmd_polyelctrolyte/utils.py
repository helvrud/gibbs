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
