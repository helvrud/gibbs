#%%
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import plotly.express as px
#%%
mc_df = pd.read_csv('mc_20_alpha_0.csv')
md_df = pd.read_csv('md_20_alpha_0.csv')
#%%
mc_df.side = mc_df.side.astype('category')
px.scatter(mc_df, x='step', y='cation', color ='side')
# %%
px.scatter(md_df, y='Pressure')
# %%
df = md_df.loc[:,md_df.columns.str.contains("Re_12")]
df = df.melt(value_vars = df.columns, ignore_index=False)
px.scatter(df, y='value', color = 'variable')

# %%
import numpy as np
def autocorrelation(X):
    # Thanks to https://www.packtpub.com/mapt/book/big_data_and_business_intelligence/9781783553358/7/ch07lvl1sec75/autocorrelation
    data = X
    y = data - np.mean(data)
    norm = np.sum(y ** 2)
    acf = np.correlate(y, y, mode='full')/norm
    acf = acf[len(y)-1:]
    acf_bool = abs(acf) > 1/np.e
    argmin = acf_bool.argmin()
    if not acf_bool[argmin:argmin<<1].any():
        tau = argmin
    else:
        print ('WARNING acf is strange')
        acf_bool_i = acf_bool[::-1]
        index = acf_bool_i.argmax()
        tau = len(acf) - index

    #~ tau = sum(abs(acf) > 1/np.e)+1
    return [acf, tau]
# %%
acf = autocorrelation(mc_df.loc[mc_df['side']==1]['cation'])[0]
# %%
px.scatter(y = acf)
# %%
acf
# %%
