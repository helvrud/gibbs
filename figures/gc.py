import pandas as pd    
from veusz_embed import *
gibbs_data_path = "../data/gel_all_data.pkl"
gc_data_path = "../data/GC.pkl"

gibbs_raw = pd.read_pickle(gibbs_data_path)
gc_raw = pd.read_pickle(gc_data_path)

Navogadro = 6.022e23 # 1/mol
unit_of_length = 0.35 # nm
unit = (unit_of_length*1e-9)**3*Navogadro*1000 # l/mol
MPC = 30 
Ngel = MPC*16+8



gibbs_raw['delta_P_bar_mean'] = gibbs_raw.delta_P_Pa_mean * 1e-5
gibbs_raw['delta_P_bar_err'] = gibbs_raw.delta_P_Pa_err * 1e-5


gibbs_df = pd.DataFrame()
for (idx, group), color in zip(gibbs_raw.groupby(by = 'n_pairs'), color_cycle):
    group = group.sort_values(by = 'gel_density')
    Ccl = np.array([list(group.c_s_mol_mean), list(group.c_s_mol_err)])
    phi = np.array(group.gel_density)
    
    P = np.array([list(group.delta_P_bar_mean), list(group.delta_P_bar_err)])
    n_pairs = list(group.n_pairs)[0]
    NNa = list(group.cation_salt_mean + group.cation_gel_mean)[0]

    Vtot = np.array(list(group.volume_gel + group.volume_salt))/Ngel*unit # l/mol
    
    gibbs_df = gibbs_df.append({'Ncl':n_pairs, 'P':P, 'phi':phi, 'cs':Ccl, 'Vtot': Vtot[0], 'NNa':NNa}, ignore_index = True)




gibbs_df = gibbs_df.sort_values(by='Ncl',ignore_index = True)


(fig_PV, graph_PV, xy)  = vplot([],[], xlog = True)
(fig_CV, graph_CV, xy)  = vplot([],[], xlog = True, ylog = True)
(fig_NV, graph_NV, xy)  = vplot([],[], xlog = True)
(fig_Nmu, graph_Nmu, xy)  = vplot([],[], xlog = True)















cs_5 = []
cs_10 = []
VV_closed = []
for (index, row), color in zip(gibbs_df.iterrows(), color_cycle):    


    
    print (index)
    phi = row.phi  # mol/l
    Vtot = row.Vtot  # l/mol
    VV_closed.append(Vtot)
    V = 1/phi      # l/mol
    P = row.P
    Ccl = row.cs
    Ncl_closed = row.Ncl / Ngel /Vtot * np.ones(len(phi))
    Ncl_closed_2 = row.Ncl / Ngel  * np.ones(len(phi))
    # Ncl = row.Ncl / Ngel*np.ones(len(phi))
    # Ncl = row.Ncl *np.ones(len(phi))
    # Ncl = row.NNa *np.ones(len(phi))

    idx5 = (abs(P[0] - 5  ) == min(abs(P[0] - 5  ))).argmax()
    idx10 = (abs(P[0] - 10  ) == min(abs(P[0] - 10  ))).argmax()
    

    P5 = P[0][idx5]
    P10 = P[0][idx10]

    #Ccl0 = Ncl_closed[0] / Vtot
    Ccl5 = Ccl[0][idx5]
    Ccl10 = Ccl[0][idx10]
    
    Ncl0 = Ncl_closed[0]
    Ncl5 = Ncl_closed[idx5]
    Ncl10 = Ncl_closed[idx10]

    Ncl0_2 = Ncl_closed_2[0]
    Ncl5_2 = Ncl_closed_2[idx5]
    Ncl10_2 = Ncl_closed_2[idx10]

    
    cs_5.append(Ccl5)
    cs_10.append(Ccl10)
    phi5 = phi[idx5]
    phi10 = phi[idx10]
    
    V0 = Vtot
    V5 = V[idx5]
    V10 = V[idx10]

    print (color)
    

    (fig_PV, graph_PV, xy) = vplot(V, P, xname = f'GB_phi'+str(row.Ncl), yname = f'GB_P'+str(row.Ncl), g=fig_PV, marker='none', color = color)
    xy.ErrorBarLine.width.val = '0.5pt'
    
    (fig_PV, graph_PV, xy) = vplot([V5], [P5], xname = 'GB_phi_5'+str(row.Ncl), yname = f'GB_P_5'+str(row.Ncl), g = fig_PV, marker='square', color = color )
    xy.markerSize.val = '4pt'
    xy.MarkerFill.color.val = color
    (fig_PV, graph_PV, xy) = vplot([V10], [P10], xname = 'GB_phi_10'+str(row.Ncl), yname = f'GB_P_10'+str(row.Ncl), g = fig_PV, marker='cross', color = color )
    xy.markerSize.val = '4pt'
    xy.MarkerFill.color.val = color


    (fig_CV, graph_CV, xy) = vplot(V, Ccl, xname = f'GB_phi{row.Ncl}_V0{V0}', yname = f'GB_Ccl{row.Ncl}_V0{V0}', g = fig_CV, marker='none', color = color)

    #(fig_CV, graph_CV, xy) = vplot([V0], [Ccl0], xname = f'GB_phi_0'+str(row.Ncl), yname = 'GB_Ccl_0'+str(row.Ncl), g = fig_CV, marker='circle', color = color )
    #xy.markerSize.val = '4pt'
    #xy.MarkerFill.color.val = color
    (fig_CV, graph_CV, xy) = vplot([V5], [Ccl5], xname = f'GB_phi_5'+str(row.Ncl), yname = f'GB_Ccl_5{row.Ncl}_V0{V0}', g = fig_CV, marker='square', color = color )
    xy.markerSize.val = '4pt'
    xy.MarkerFill.color.val = color
    (fig_CV, graph_CV, xy) = vplot([V10], [Ccl10], xname = f'GB_phi_10'+str(row.Ncl), yname = f'GB_Ccl_10'+str(row.Ncl), g = fig_CV, marker='cross', color = color )
    xy.markerSize.val = '4pt'
    xy.MarkerFill.color.val = color

    (fig_NV, graph_NV, xy) = vplot(V, Ncl_closed, xname = f'GB_phi'+str(row.Ncl), yname = f'GB_Ncl'+str(row.Ncl), g = fig_NV, marker='none', color = color)

    (fig_NV, graph_NV, xy) = vplot([V0], [Ncl0], xname = f'GB_phi_0'+str(row.Ncl), yname = f'GB_Ncl_0'+str(row.Ncl), g = fig_NV, marker='circle', color = color )
    xy.markerSize.val = '4pt'
    xy.MarkerFill.color.val = color
    (fig_NV, graph_NV, xy) = vplot([V5], [Ncl5], xname = f'GB_phi_5'+str(row.Ncl), yname = f'GB_Ncl_5'+str(row.Ncl), g = fig_NV, marker='square', color = color )
    xy.markerSize.val = '4pt'
    xy.MarkerFill.color.val = color
    #(fig_NV, graph_NV, xy) = vplot([V10], [Ncl10], xname = f'GB_phi_10'+str(row.Ncl), yname = f'GB_Ncl_10'+str(row.Ncl), g = fig_NV, marker='cross', color = color )
    #xy.markerSize.val = '4pt'
    #xy.MarkerFill.color.val = color




    (fig_Nmu, graph_Nmu, xy) = vplot(Ncl_closed_2, Ccl, xname = f'GB_Ncl'+str(row.Ncl), yname = f'GB_phi'+str(row.Ncl), g = fig_Nmu, marker='none', color = color)

    (fig_Nmu, graph_Nmu, xy) = vplot([Ncl5_2], [Ccl5], xname = f'GB_Ncl_5'+str(row.Ncl), yname = f'GB_phi_5'+str(row.Ncl), g = fig_Nmu, marker='square', color = color )
    xy.markerSize.val = '4pt'
    xy.MarkerFill.color.val = color
    (fig_Nmu, graph_Nmu, xy) = vplot([Ncl10_2], [Ccl10], xname = f'GB_Ncl_10'+str(row.Ncl), yname = f'GB_phi_10'+str(row.Ncl), g = fig_Nmu, marker='cross', color = color )
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

gc_raw_ =  gc_raw.loc[[1,6,11,12,15,18,20,24,27,30,33,40]]
gc_raw__ = gc_raw.loc[[1,6,10,12,15,18,21,23,27,30,34,40]]
indicies_to_plot_  = [1,6,11,12,15,18,20,24,27,30,33,40]
indicies_to_plot = [1,6,10,12,13,15,18,21,24,27,30,34]
indicies_to_plot = []
#indicies_to_plot = indicies_to_plot + indicies_to_plot_
#indicies_to_plot = np.sort(np.unique(indicies_to_plot)) 
i = 0 
#for (idx, group), color in zip(gc_raw.groupby(by = 'cs'), color_cycle):
for (index, row), color in zip(gc_raw.iterrows(), color_cycle):
    #print (row)
    V = row.V # l/mol per one gel segment
    V0 = row.V_eq # l/mol per one gel segment
    

    P = row.P
    
    idx0 = np.where(V==V0)[0][0]
    idx5 = (abs(P[0] - 5  ) == min(abs(P[0] - 5  ))).argmax()
    idx10 = (abs(P[0] - 10  ) == min(abs(P[0] - 10  ))).argmax()
    V5 = V[idx5]
    V10 = V[idx10]
    
    if index in indicies_to_plot: 
        V0 = VV_closed[i]
        i = i+1
    Ncharges = 488
    
    
    
    P0 = P[0][idx0]
    P5 = P[0][idx5]
    P10 = P[0][idx10]

    Ccl = row.cs*np.ones(len(V))
    Ccl0 = row.cs
    Ccl5 = Ccl[idx5]
    Ccl10 = Ccl[idx10]

    #Ncl = row.NCl_gel[0] / Ngel + (V0 - row.V)*row.cs
    #Ncl_err = row.NCl_gel[1] / Ngel 
    Ncl_open = (row.NCl_gel[0] / Ncharges + (V0 - V)*row.cs  ) / V0
    Ncl_open_2 = (row.NCl_gel[0] / Ncharges + (V0 - V)*row.cs  ) 
    #Ncl_open = (row.NCl_gel[0] / Ncharges + (V0 - V)*row.cs  ) 
    #Ncl = (row.NCl_gel[0] / Ncharges + (V0 - V)*row.cs  ) 
    #Ncl = (row.NNa_gel[0] + (V0 - row.V)*row.cs * Ngel )
    Ncl_open_err = row.NCl_gel[1] / V0/ Ncharges  # per charge per volume of the box
    Ncl_open_err_2 = row.NCl_gel[1] / Ncharges  # per charge per volume of the box

    Ncl0  = Ncl_open[idx0]
    Ncl5  = Ncl_open[idx5]
    Ncl10 = Ncl_open[idx10]
    Ncl0_2  = Ncl_open_2[idx0]
    Ncl5_2  = Ncl_open_2[idx5]
    Ncl10_2 = Ncl_open_2[idx10]

    phi = 1./V
    phi0 = 1./V0
    phi5 = 1./V5
    phi10 = 1./V10
    
    PP0.append(P0); 
    PP5.append(P5); PP10.append(P10)
    CCcl0.append(Ccl0); CCcl5.append(Ccl5); CCcl10.append(Ccl10)
    VV0.append(V0); VV5.append(V5); VV10.append(V10)
    
    
    #if index in indicies_to_plot: 
    (fig_PV, graph_PV, xy) = vplot(V, P, xname = f'GC_phi{row.cs}_V0{V0}', yname = f'GC_P{row.cs}_V0{V0}', g = fig_PV, marker='none',color=color)
    xy.PlotLine.width.val = '1pt'
    xy.ErrorBarLine.width.val = '0.5pt'
    (fig_PV, graph_PV, xy) = vplot([V0], [P0], xname = f'GC_phi0{row.cs}_V0{V0}', yname = f'GC_P0{row.cs}_V0{V0}', g = fig_PV, marker='circle',color=color )
    xy.markerSize.val = '4pt'
    (fig_PV, graph_PV, xy) = vplot([V5], [P5], xname = f'GC_phi5{row.cs}_V0{V0}', yname = f'GC_P5{row.cs}_V0{V0}', g = fig_PV, marker='square',color=color )
    xy.markerSize.val = '4pt'
    (fig_PV, graph_PV, xy) = vplot([V10], [P10], xname = 'GC_phi10{row.cs}_V0{V0}', yname = f'GC_P10{row.cs}_V0{V0}', g = fig_PV, marker='cross',color=color )
    xy.markerSize.val = '4pt'


    #if index in indicies_to_plot: 
    (fig_CV, graph_CV, xy) = vplot(V, Ccl, xname = f'GC_phi{row.cs}_V0{V0}', yname = f'GC_Ccl{row.cs}_V0{V0}', g = fig_CV, marker='none',color=color)
    xy.PlotLine.width.val = '1pt'
    (fig_CV, graph_CV, xy) = vplot([V0], [Ccl0], xname = f'GC_phi0{row.cs}_V0{V0}', yname = f'GC_Ccl0{row.cs}_V0{V0}', g = fig_CV, marker='circle',color=color )
    xy.markerSize.val = '4pt'
    (fig_CV, graph_CV, xy) = vplot([V5], [Ccl5], xname = f'GC_phi5{row.cs}_V0{V0}', yname = f'GC_Ccl5{row.cs}_V0{V0}', g = fig_CV, marker='square',color=color )
    xy.markerSize.val = '4pt'
    (fig_CV, graph_CV, xy) = vplot([V10], [Ccl10], xname = f'GC_phi10{row.cs}_V0{V0}', yname = f'GC_Ccl10{row.cs}_V0{V0}', g = fig_CV, marker='cross',color=color )
    xy.markerSize.val = '4pt'
    

    #if index in indicies_to_plot: 
    (fig_NV, graph_NV, xy) = vplot(V, [Ncl_open, Ncl_open_err], xname = f'GC_phi{row.cs}_V0{V0}', yname = f'GC_Ncl{row.cs}_V0{V0}',  g = fig_NV, marker='none',color=color)
    xy.PlotLine.width.val = '1pt'
    (fig_NV, graph_NV, xy) = vplot([V0], [Ncl0], xname = f'GC_phi0{row.cs}_V0{V0}', yname = f'GC_Ncl0{row.cs}_V0{V0}',     g = fig_NV, marker='circle',color=color )
    xy.markerSize.val = '4pt'
    (fig_NV, graph_NV, xy) = vplot([V5], [Ncl5], xname = f'GC_phi5{row.cs}_V0{V0}', yname = f'GC_Ncl5{row.cs}_V0{V0}',     g = fig_NV, marker='square',color=color )
    xy.markerSize.val = '4pt'
    (fig_NV, graph_NV, xy) = vplot([V10], [Ncl10], xname = f'GC_phi10{row.cs}_V0{V0}', yname = f'GC_Ncl10{row.cs}_V0{V0}', g = fig_NV, marker='cross',color=color )
    xy.markerSize.val = '4pt'
    
    
    #if index in indicies_to_plot: 
    (fig_Nmu, graph_Nmu, xy) = vplot([Ncl_open_2, Ncl_open_err_2], Ccl, xname = f'GC_Ncl{row.cs}_V0{V0}', yname = f'GC_phi{row.cs}_V0{V0}',  g = fig_Nmu, marker='none',color=color)
    xy.PlotLine.width.val = '1pt'
    (fig_Nmu, graph_Nmu, xy) = vplot([Ncl0_2], [Ccl0], xname = f'GC_Ncl0{row.cs}_V0{V0}', yname = f'GC_phi0{row.cs}_V0{V0}',     g = fig_Nmu, marker='circle',color=color )
    xy.markerSize.val = '4pt'
    (fig_Nmu, graph_Nmu, xy) = vplot([Ncl5_2], [Ccl5],  xname = f'GC_Ncl5{row.cs}_V0{V0}', yname = f'GC_phi5{row.cs}_V0{V0}',     g = fig_Nmu, marker='square',color=color )
    xy.markerSize.val = '4pt'
    (fig_Nmu, graph_Nmu, xy) = vplot([Ncl10_2], [Ccl10],  xname = f'GC_Ncl10{row.cs}_V0{V0}', yname = f'GC_phi10{row.cs}_V0{V0}', g = fig_Nmu, marker='cross',color=color )
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

#graph_NV.y.max.val=0.38
#graph_NV.y.min.val=0.01
graph_NV.y.log.val = True
graph_NV.x.log.val = True
graph_NV.x.max.val=11.79
graph_NV.x.min.val=0.7

graph_NV.x.label.val = 'hydrogel volume, V, [l/mol]'
graph_NV.y.label.val = 'Number of Cl ions per gel monomer, N_{Cl}, [mol/mol]'


graph_Nmu.y.label.val = 'Salinity, c_{s}, [mol/l]'
graph_Nmu.x.label.val = 'Number of Cl ions per gel monomer, N_{Cl}, [mol/mol]'
graph_Nmu.y.log.val = True
graph_Nmu.x.log.val = True
graph_Nmu.x.max.val=1
graph_Nmu.x.min.val=1e-3
graph_Nmu.y.max.val=1
graph_Nmu.y.min.val=1e-3



key = graph_PV.Add('key')
key.vertPosn.val = 'top'
key.horzPosn.val = 'left'
key.Border.hide.val  = True


import os
fig_CV.Save('fig_CV.vsz')
fig_PV.Save('fig_PV.vsz')
fig_NV.Save('fig_NV.vsz')
fig_Nmu.Save('fig_Nmu.vsz')
os.popen('veusz fig_CV.vsz')
os.popen('veusz fig_PV.vsz')
os.popen('veusz fig_NV.vsz')
os.popen('veusz fig_Nmu.vsz')


