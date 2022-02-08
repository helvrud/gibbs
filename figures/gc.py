import pandas as pd    
from veusz_embed import *
gibbs_data_path = "../data/gel_all_data.pkl"
gc_data_path = "../data/GC.pkl"

gibbs_raw = pd.read_pickle(gibbs_data_path)
gc_raw = pd.read_pickle(gc_data_path)





gibbs_raw['delta_P_bar_mean'] = gibbs_raw.delta_P_Pa_mean * 1e-5
gibbs_raw['delta_P_bar_err'] = gibbs_raw.delta_P_Pa_err * 1e-5


(fig_PV, graph_PV, xy)  = vplot([],[], xlog = True)
(fig_CV, graph_CV, xy)  = vplot([],[], xlog = True, ylog = True)
#for (idx, group), color in zip(gc_raw.groupby(by = 'cs'), color_cycle):
for index, row in gc_raw.iterrows():
    #print (row)
    V = row.V
    V0 = row.V_eq

    P = row.P
    idx0 = np.where(V==V0)[0][0]
    idx5 = (abs(P[0] - 5  ) == min(abs(P[0] - 5  ))).argmax()
    idx10 = (abs(P[0] - 10  ) == min(abs(P[0] - 10  ))).argmax()
    V5 = V[idx5]
    V10 = V[idx10]
    
    P0 = P[0][idx0]
    P5 = P[0][idx5]
    P10 = P[0][idx10]

    CCl = row.cs*np.ones(len(V))
    CCl0 = row.cs
    CCl5 = CCl[idx5]
    CCl10 = CCl[idx10]

    phi = 1./V
    phi0 = 1./V0
    phi5 = 1./V5
    phi10 = 1./V10
    
    (fig_PV, graph_PV, xy) = vplot(phi, P, xname = 'GC_phi'+str(row.cs), yname = 'GC_P'+str(row.cs), g = fig_PV, marker='none')
    (fig_PV, graph_PV, xy) = vplot([phi0], [P0], xname = 'GC_phi0'+str(row.cs), yname = 'GC_P0'+str(row.cs), g = fig_PV, marker='circle' )
    xy.markerSize.val = '4pt'
    (fig_PV, graph_PV, xy) = vplot([phi5], [P5], xname = 'GC_phi5'+str(row.cs), yname = 'GC_P5'+str(row.cs), g = fig_PV, marker='square' )
    xy.markerSize.val = '4pt'
    (fig_PV, graph_PV, xy) = vplot([phi10], [P10], xname = 'GC_phi10'+str(row.cs), yname = 'GC_P10'+str(row.cs), g = fig_PV, marker='cross' )
    xy.markerSize.val = '4pt'


    (fig_CV, graph_CV, xy) = vplot(phi, CCl, xname = 'GC_phi'+str(row.cs), yname = 'GC_CCl'+str(row.cs), g = fig_CV, marker='none')
    (fig_CV, graph_CV, xy) = vplot([phi0], [CCl0], xname = 'GC_phi0'+str(row.cs), yname = 'GC_CCl0'+str(row.cs), g = fig_CV, marker='circle' )
    xy.markerSize.val = '4pt'
    (fig_CV, graph_CV, xy) = vplot([phi5], [CCl5], xname = 'GC_phi5'+str(row.cs), yname = 'GC_CCl5'+str(row.cs), g = fig_CV, marker='square' )
    xy.markerSize.val = '4pt'
    (fig_CV, graph_CV, xy) = vplot([phi10], [CCl10], xname = 'GC_phi10'+str(row.cs), yname = 'GC_CCl10'+str(row.cs), g = fig_CV, marker='cross' )
    xy.markerSize.val = '4pt'
    



for (idx, group), color in zip(gibbs_raw.groupby(by = 'n_pairs'), color_cycle):
    group = group.sort_values(by = 'gel_density')

    CCl = np.array([list(group.c_s_mol_mean), list(group.c_s_mol_err)])
    phi = np.array(group.gel_density)
    P = np.array([list(group.delta_P_bar_mean), list(group.delta_P_bar_err)])


    idx5 = (abs(P[0] - 5  ) == min(abs(P[0] - 5  ))).argmax()
    idx10 = (abs(P[0] - 10  ) == min(abs(P[0] - 10  ))).argmax()
    

    P5 = P[0][idx5]
    P10 = P[0][idx10]

    CCl5 = CCl[0][idx5]
    CCl10 = CCl[0][idx10]

    phi5 = phi[idx5]
    phi10 = phi[idx10]
    print (color)

    (fig_PV, graph_PV, xy) = vplot(phi, P, xname = 'GB_phi'+str(idx), yname = 'GB_P'+str(idx), g=fig_PV, color = color)
    (fig_PV, graph_PV, xy) = vplot([phi5], [P5], xname = 'GB_phi5'+str(idx), yname = 'GB_P5'+str(idx), g = fig_PV, marker='square', color = color )
    xy.markerSize.val = '4pt'
    xy.MarkerFill.color.val = color
    (fig_PV, graph_PV, xy) = vplot([phi10], [P10], xname = 'GB_phi10'+str(idx), yname = 'GB_P10'+str(idx), g = fig_PV, marker='cross', color = color )
    xy.markerSize.val = '4pt'
    xy.MarkerFill.color.val = color

    (fig_CV, graph_CV, xy) = vplot(phi, CCl, xname = 'GB_phi'+str(idx), yname = 'GB_CCl'+str(idx), g = fig_CV, marker='none', color = color)
    (fig_CV, graph_CV, xy) = vplot([phi5], [CCl5], xname = 'GB_phi5'+str(idx), yname = 'GB_CCl5'+str(idx), g = fig_CV, marker='square', color = color )
    xy.markerSize.val = '4pt'
    xy.MarkerFill.color.val = color
    (fig_CV, graph_CV, xy) = vplot([phi10], [CCl10], xname = 'GB_phi10'+str(idx), yname = 'GB_CCl10'+str(idx), g = fig_CV, marker='cross', color = color )
    xy.markerSize.val = '4pt'
    xy.MarkerFill.color.val = color


from veusz_embed import y_axis, x_axis

graph_PV.y.max.val=5
graph_PV.y.min.val=-0.56        
graph_PV.x.log.val = True
graph_PV.x.label.val = 'hydrogel density, \\varphi, [mol/l]'
graph_PV.y.label.val = '\\Delta P = P - P_{res}, [bar]'

#graph_CV.y.max.val=5
#graph_CV.y.min.val=-0.56        
graph_CV.x.log.val = True
graph_CV.y.log.val = True
graph_CV.x.label.val = 'hydrogel density, \\varphi, [mol/l]'
graph_CV.y.label.val = 'Salinity, c_{s}, [mol/l]'




key = graph.Add('key')
key.vertPosn.val = 'top'
key.horzPosn.val = 'left'
key.Border.hide.val  = True









