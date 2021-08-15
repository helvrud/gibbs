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

def autocorrelation(X):
    import numpy as np
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

def int_steps_recommended(server, client):
    pass