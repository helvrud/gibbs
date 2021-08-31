#%%
import numpy as np
Re = np.loadtxt('Re_sample(int_steps_100).csv', delimiter = ',')
pressure = np.loadtxt('pressure_sample.csv', delimiter = ',')
# %%
import matplotlib.pyplot as plt
# %%
plt.plot(Re[:,0])
# %%
import utils
# %%
tau_Re = max([utils.get_tau(re) for re in Re.T])
tau_Pressure = utils.get_tau(pressure)
# %%
tau_Re
# %%
tau_Pressure
# %%
utils.correlated_data_mean_err(np.mean(Re, axis = 1),tau_Re)
# %%
