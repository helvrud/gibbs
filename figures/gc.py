
def create_g(box_l):
    from gel import gel
    # ~ print ('###')
    g = gel()
    g.sigma = sigma
    g.USERNAME = 'kvint'
    
    g.box_l = box_l
    # ~ g.MPC = 5
    g.swap = False
    g.p['K'] = pK
    if np.abs(g.p['K'])==np.infty:g.p['H']=np.infty
    
    g.p['Cl'] = -np.log10(cs)

    g.p['Ca'] = np.infty
    g.p['Na'] = -np.log10(cs)
    #g.p['H'] = 7.0
    g.eq_steps = 10000
    g.N_Samples = N_Samples
    g.lB = lB
    print('created gel:', g)    # important! this string generates all the names of the object, i.e. g.name, g.fname etc
    return g



def load_g(box_l):
    
    global g
    
    g = create_g(box_l)
    try:
        g = g.load_merge(scp =scp)
    


        n_samples = len(g.Samples['pressure'])
        print (g.name, 'Loaded...', 'number of samples: ', n_samples)
        g.keys['re'] = ['Na', 'Cl']
        if g.p['K'] != np.inf: g.keys['re'].append('PA')

        if 'mindist' in g.keys['md']: g.keys['md'].remove('mindist')
        if n_samples>50:
            g.Pearson(keys = g.keys['md']+g.keys['re'])
            #g.VMD()
        print ();
    
        return g
    except FileNotFoundError:
        pass
    
if __name__ == '__main__':
    import pandas as pd    
    from veusz_embed import *
    gibbs_data_path = "../data/gel_all_data.pkl"
    gc_data_path = "../data/GC.pkl"

    gibbs_raw = pd.read_pickle(gibbs_data_path)
    gc_raw = pd.read_pickle(gc_data_path)





    gibbs_raw['delta_P_bar_mean'] = gibbs_raw.delta_P_Pa_mean * 1e-5
    gibbs_raw['delta_P_bar_err'] = gibbs_raw.delta_P_Pa_err * 1e-5


    (fig, graph, xy)  = vplot([],[])
    #for (idx, group), color in zip(gc_raw.groupby(by = 'cs'), color_cycle):
    for index, row in gc_raw.iterrows():
        print (row)
        P = row.P
        V = row.V
        phi = 1./V
        vplot(phi,P, xname = 'GC_phi'+str(row.cs), yname = 'GC_P'+str(row.cs), g = fig, marker='none', xlog = True)
    




    for (idx, group), color in zip(gibbs_raw.groupby(by = 'n_pairs'), color_cycle):
        group = group.sort_values(by = 'gel_density')
        vplot(
            list(group.gel_density), 
            [list(group.delta_P_bar_mean), list(group.delta_P_bar_err)],
            xname = 'x'+str(idx), yname = 'y'+str(idx), 
            xlog = True, ylog = False,
            g=fig, color = color
            )
        #xy.key.val = 'c_{s} = {}'.format(float(group.c_s_reservoir_mol.head(1))
        #xy.key.val = 'c_{{s}} = {:.2e}'.format(float(group.c_s_reservoir_mol.head(1))) 








    
    from veusz_embed import y_axis, x_axis
    
    y_axis.max.val=5
    y_axis.min.val=-2        
    x_axis.label.val = '\\phi'
    y_axis.label.val = 'P' 












