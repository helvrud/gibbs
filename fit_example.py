x0 = np.random.random_sample(size=4)
#c_s = gibbs_raw.c_s_mol_mean.to_numpy()
#c_gel = gibbs_raw.c_gel.to_numpy()
y = np.linspace(0.004, 0.08) #c_gel
x = np.linspace(0.002, 0.8) # c_s
fit_ = lambda x,y: 1.5*y + 0.5*y**2 + 3*x
z = fit_(*np.meshgrid(x,y))
#delta_P = gibbs_raw.delta_P_Pa_mean.to_numpy()

# %%
c_s = list(range(0,5))*5
c_gel = list([ii for  i in range(0,5) for ii in [i]*5])
fit_ = lambda x,y: 1.5*y + 0.5*y**2 + 3*x
delta_P = [fit_(x_,y_) for x_, y_ in zip(c_s,c_gel)]
# %%
#lm = solve(fit_function, c_s, c_gel, delta_P, x0)
lm = solve(fit_function, c_s, c_gel, delta_P, np.random.random_sample(size=3))
fit = np.vectorize(functools.partial(fit_function, x = lm.x))
