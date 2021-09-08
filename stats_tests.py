#%%
import numpy as np
import matplotlib.pyplot as plt
import utils
Re = np.loadtxt('Re_sample(int_steps_100).csv', delimiter = ',')
pressure = np.loadtxt('pressure_sample(int_steps_100).csv', delimiter = ',')
#%%
plt.plot(Re[:,0])
# %%
tau_Re = max([utils.get_tau(re) for re in Re.T])
utils.correlated_data_mean_err(np.mean(Re, axis = 1),tau_Re)
# %%
tau_Re
# %%
utils.ljung_box_white_noise(Re[:,0])
# %%
for chunk in np.array_split(Re[:,0], int(len(Re[:,0])/(tau_Re*10))):
    print(utils.check_stationarity(chunk))
# %%
plt.plot(Re[:,0][:int(tau_Re)*50])
# %%
plt.plot(pressure[:50])
# %%
tau_P = utils.get_tau(pressure)
tau_P
# %%
for chunk in np.array_split(pressure, int(len(pressure)/(tau_P*15))):
    print(utils.check_stationarity(chunk))
# %%
