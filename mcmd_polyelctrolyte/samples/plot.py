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
