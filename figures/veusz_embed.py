#%%
import veusz.embed as veusz
import numpy as np

def addxy(graph,
        x_dataname='',
        y_dataname='',
        marker='circle', markersize='2pt', color = 'black', style = 'dotted',
        keylabel = '',
        xname='', yname='',
        xlog=False, ylog=False):
    # adds an xy plot to a graph
    global xy
    xy = graph.Add('xy')

    xy.xData.val = x_dataname
    xy.yData.val = y_dataname
    xy.marker.val = marker
    xy.MarkerFill.color.val = color
    xy.MarkerLine.color.val = 'transparent'

    xy.markerSize.val = markersize

    xy.PlotLine.width.val = '2pt'
    xy.PlotLine.style.val = style
    xy.PlotLine.color.val = color
    xy.ErrorBarLine.color.val = color
    # ~ xy.PlotLine.hide.val = not PlotLine


    keylabels = []
    for i in graph.childnames:
        if i[:2] == 'xy':
            exec('keylabels.append(graph.'+i+'.key.val)')

    if not keylabel in keylabels: xy.key.val = keylabel
    x_axis = graph.x
    y_axis = graph.y
    x_axis.label.val = xname
    x_axis.log.val = xlog
    y_axis.label.val = yname
    y_axis.log.val = ylog

    #~ y_axis.min.val = -1.1
    #~ y_axis.max.val = 1.1

    #~ x_axis.min.val = 0.25
    #~ x_axis.max.val = 0.6

    xy.ErrorBarLine.width.val = '2pt'

def vplot(  x=[],y=[],
            xname = 'x', yname = 'y',
            xlog = False, ylog = False,
            color = 'black',
            style='dotted', PlotLine = True, marker = 'circle', markersize = '2pt', keylabel='', title='notitle',
            g = None, graph=None  ):

    global xy, x_axis, y_axis, x_data, y_data, x_dataname, y_dataname
    figsize = 16
    aspect = 1.6
    if x == []:
        x = range(len(y))


    if g == None:
        g = veusz.Embedded(title)
        g.EnableToolbar()
        page = g.Root.Add('page')
        graph = page.Add('graph')
    else:
        if type(graph) != veusz.WidgetNode:
            page = g.Root.page1
            graph = page.graph1
        else:
            print(graph)
            print()
            print()
            print()
            print()
    page.width.val = str(figsize)+'cm'
    page.height.val = str(figsize / aspect)+'cm'


    x_dataname  = xname
    y_dataname  = yname

    if len(np.shape(x)) == 2:
        x_data = x[0]
        x_data_err = x[1]
        g.SetData(x_dataname, x_data, symerr = x_data_err)
    else:
        x_data = x
        g.SetData(x_dataname, x_data)
    if len(np.shape(y)) == 2:
        print("Y errors notified")
        y_data = y[0]
        y_data_err = y[1]
        g.SetData(y_dataname, y_data, symerr = y_data_err)
    else:
        y_data = y
        g.SetData(y_dataname, y_data)



    addxy(graph, x_dataname = x_dataname, y_dataname = y_dataname, marker=marker, markersize=markersize, color=color, style = style, keylabel = keylabel, xname=xname, yname=yname, xlog=xlog, ylog=ylog)
    if len(x_data) == 1:
        xy.MarkerLine.color.val = xy.MarkerFill.color.val;xy.MarkerFill.color.val = 'white'; xy.MarkerLine.width.val = '1.0pt'
    #~ xy_sim.ErrorBarLine.transparency.val = 50


    return g

matplotlib_colors = [
    '#1f77b4',
    '#ff7f0e',
    '#2ca02c',
    '#d62728',
    '#9467bd',
    '#8c564b',
    '#e377c2',
    '#7f7f7f',
    '#bcbd22',
    '#17becf',
    ]

from itertools import cycle

color_cycle = cycle(matplotlib_colors)
#%%