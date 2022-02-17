import pandas as pd    
from veusz_embed import *
gibbs_data_path = "../data/gel_all_data.pkl"
gc_data_path = "../data/GC.pkl"

gibbs_raw = pd.read_pickle(gibbs_data_path)
gc_raw = pd.read_pickle(gc_data_path)





gibbs_raw['delta_P_bar_mean'] = gibbs_raw.delta_P_Pa_mean * 1e-5
gibbs_raw['delta_P_bar_err'] = gibbs_raw.delta_P_Pa_err * 1e-5


gibbs_df = pd.DataFrame()
for (idx, group), color in zip(gibbs_raw.groupby(by = 'n_pairs'), color_cycle):
    group = group.sort_values(by = 'gel_density')
    Ccl = np.array([list(group.c_s_mol_mean), list(group.c_s_mol_err)])
    phi = np.array(group.gel_density)
    
    P = np.array([list(group.delta_P_bar_mean), list(group.delta_P_bar_err)])
    n_pairs = list(group.n_pairs)[0]
    
    gibbs_df = gibbs_df.append({'Ncl':n_pairs, 'P':P, 'phi':phi, 'cs':Ccl}, ignore_index = True)

gibbs_df = gibbs_df.sort_values(by='Ncl',ignore_index = True)


(fig_PV, graph_PV, xy)  = vplot([],[], xlog = True)
(fig_CV, graph_CV, xy)  = vplot([],[], xlog = True, ylog = True)















cs_5 = []
cs_10 = []
for (index, row), color in zip(gibbs_df.iterrows(), color_cycle):    


    
    print (index)
    phi = row.phi  # l/mol
    V = 1/phi      # mol/l
    P = row.P
    Ccl = row.cs
    Ncl = row.Ncl*np.ones(len(phi))


    idx5 = (abs(P[0] - 5  ) == min(abs(P[0] - 5  ))).argmax()
    idx10 = (abs(P[0] - 10  ) == min(abs(P[0] - 10  ))).argmax()
    

    P5 = P[0][idx5]
    P10 = P[0][idx10]

    Ccl5 = Ccl[0][idx5]
    Ccl10 = Ccl[0][idx10]
    cs_5.append(Ccl5)
    cs_10.append(Ccl10)
    phi5 = phi[idx5]
    phi10 = phi[idx10]
    V5 = V[idx5]
    V10 = V[idx10]

    print (color)
    

    (fig_PV, graph_PV, xy) = vplot(V, P, xname = 'GB_phi'+str(row.Ncl), yname = 'GB_P'+str(row.Ncl), g=fig_PV, marker='none', color = color)
    xy.ErrorBarLine.width.val = '0.5pt'
    
    (fig_PV, graph_PV, xy) = vplot([V5], [P5], xname = 'GB_phi_5'+str(row.Ncl), yname = 'GB_P_5'+str(row.Ncl), g = fig_PV, marker='square', color = color )
    xy.markerSize.val = '4pt'
    xy.MarkerFill.color.val = color
    (fig_PV, graph_PV, xy) = vplot([V10], [P10], xname = 'GB_phi_10'+str(row.Ncl), yname = 'GB_P_10'+str(row.Ncl), g = fig_PV, marker='cross', color = color )
    xy.markerSize.val = '4pt'
    xy.MarkerFill.color.val = color


    (fig_CV, graph_CV, xy) = vplot(V, Ccl, xname = 'GB_phi'+str(row.Ncl), yname = 'GB_Ccl'+str(row.Ncl), g = fig_CV, marker='none', color = color)

    (fig_CV, graph_CV, xy) = vplot([V5], [Ccl5], xname = 'GB_phi_5'+str(row.Ncl), yname = 'GB_Ccl_5'+str(row.Ncl), g = fig_CV, marker='square', color = color )
    xy.markerSize.val = '4pt'
    xy.MarkerFill.color.val = color
    (fig_CV, graph_CV, xy) = vplot([V10], [Ccl10], xname = 'GB_phi_10'+str(row.Ncl), yname = 'GB_Ccl_10'+str(row.Ncl), g = fig_CV, marker='cross', color = color )
    xy.markerSize.val = '4pt'
    xy.MarkerFill.color.val = color









PP0 = []
PP5 = []
PP10 = []

CCcl0 = []
CCcl5 = []
CCcl10 = []

VV0 = []
VV5 = []
VV10 = []



#for (idx, group), color in zip(gc_raw.groupby(by = 'cs'), color_cycle):
for (index, row), color in zip(gc_raw.iterrows(), color_cycle):
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

    Ccl = row.cs*np.ones(len(V))
    Ccl0 = row.cs
    Ccl5 = Ccl[idx5]
    Ccl10 = Ccl[idx10]

    phi = 1./V
    phi0 = 1./V0
    phi5 = 1./V5
    phi10 = 1./V10
    
    PP0.append(P0); PP5.append(P5); PP10.append(P10)
    CCcl0.append(Ccl0); CCcl5.append(Ccl5); CCcl10.append(Ccl10)
    VV0.append(V0); VV5.append(V5); VV10.append(V10)
    
    
    (fig_PV, graph_PV, xy) = vplot(V, P, xname = 'GC_phi'+str(row.cs), yname = 'GC_P'+str(row.cs), g = fig_PV, marker='none',color=color)
    xy.PlotLine.width.val = '1pt'
    xy.ErrorBarLine.width.val = '0.5pt'
    (fig_PV, graph_PV, xy) = vplot([V0], [P0], xname = 'GC_phi0'+str(row.cs), yname = 'GC_P0'+str(row.cs), g = fig_PV, marker='circle',color=color )
    xy.markerSize.val = '4pt'
    (fig_PV, graph_PV, xy) = vplot([V5], [P5], xname = 'GC_phi5'+str(row.cs), yname = 'GC_P5'+str(row.cs), g = fig_PV, marker='square',color=color )
    xy.markerSize.val = '4pt'
    (fig_PV, graph_PV, xy) = vplot([V10], [P10], xname = 'GC_phi10'+str(row.cs), yname = 'GC_P10'+str(row.cs), g = fig_PV, marker='cross',color=color )
    xy.markerSize.val = '4pt'


    (fig_CV, graph_CV, xy) = vplot(V, Ccl, xname = 'GC_phi'+str(row.cs), yname = 'GC_Ccl'+str(row.cs), g = fig_CV, marker='none',color=color)
    xy.PlotLine.width.val = '1pt'
    (fig_CV, graph_CV, xy) = vplot([V0], [Ccl0], xname = 'GC_phi0'+str(row.cs), yname = 'GC_Ccl0'+str(row.cs), g = fig_CV, marker='circle',color=color )
    xy.markerSize.val = '4pt'
    (fig_CV, graph_CV, xy) = vplot([V5], [Ccl5], xname = 'GC_phi5'+str(row.cs), yname = 'GC_Ccl5'+str(row.cs), g = fig_CV, marker='square',color=color )
    xy.markerSize.val = '4pt'
    (fig_CV, graph_CV, xy) = vplot([V10], [Ccl10], xname = 'GC_phi10'+str(row.cs), yname = 'GC_Ccl10'+str(row.cs), g = fig_CV, marker='cross',color=color )
    xy.markerSize.val = '4pt'
    

(fig_CV, graph_CV, xy) = vplot(VV0, CCcl0, xname = 'VV0', yname = 'CCcl0', g = fig_CV, marker='none',color=color)
(fig_CV, graph_CV, xy) = vplot(VV5, CCcl5, xname = 'VV5', yname = 'CCcl5', g = fig_CV, marker='none',color=color)
(fig_CV, graph_CV, xy) = vplot(VV10, CCcl10, xname = 'VV10', yname = 'CCcl10', g = fig_CV, marker='none',color=color)

cs_5


from veusz_embed import y_axis, x_axis

graph_PV.y.max.val=5
graph_PV.y.min.val=-0.56        
graph_PV.x.log.val = True
graph_PV.x.label.val = 'hydrogel volume, V, [l/mol]'
graph_PV.y.label.val = '\\Delta P = P - P_{res}, [bar]'

#graph_CV.y.max.val=5
#graph_CV.y.min.val=-0.56        
graph_CV.x.log.val = True
graph_CV.y.log.val = True
graph_CV.x.label.val = 'hydrogel volume, V, [l/mol]'
graph_CV.y.label.val = 'Salinity, c_{s}, [mol/l]'




key = graph_PV.Add('key')
key.vertPosn.val = 'top'
key.horzPosn.val = 'left'
key.Border.hide.val  = True


import os
fig_CV.Save('fig_CV.vsz')
fig_PV.Save('fig_PV.vsz')
os.popen('veusz fig_CV.vsz')
os.popen('veusz fig_PV.vsz')



