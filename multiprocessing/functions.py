# -*- coding: utf-8 -*-
import numpy as np
import sys
from copy import copy, deepcopy
try: from pylab import find
except ImportError: from numpy import nonzero as find
try: import veusz.embed as veusz
except ImportError:
    try: import veusz
    except ImportError: pass
#import matplotlib.pyplot as plt

#############################
### Some useful functions ###
#############################


#~ A derivative by 7 datapoints
def dervec7(v,h=1):
    global f
    # Finds a derivative by 7 points
    # v - the function to derivate
    # h - step size
    n=len(v);
    f=np.zeros(n)
    for k in range(n):
        if k==0:
            f[0]=(-147.0*v[0]+360.0*v[1]-450.0*v[2]+400.0*v[3]-225.0*v[4]+72.0*v[5]-10.0*v[6])/60.0/h ;
        elif k==1:
            f[1]=(-10.0*v[0]-77.0*v[1]+150.0*v[2]-100.0*v[3]+50.0*v[4]-15.0*v[5]+2.0*v[6])/60.0/h ;
        elif k==2:
            f[2]=(2.0*v[0]-24.0*v[1]-35.0*v[2]+80.0*v[3]-30.0*v[4]+8.0*v[5]-v[6])/60.0/h ;
        elif k > 2 and k < n-3:
            f[k]=(-v[k-3]+9.0*v[k-2]-45.0*v[k-1]+45.0*v[k+1]-9.0*v[k+2]+v[k+3])/60.0/h;
        elif k==n-3:
            f[k]=(v[k-4]-8.0*v[k-3]+30.0*v[k-2]-80.0*v[k-1]+35.0*v[k]+24.0*v[k+1]-2.0*v[k+2])/60.0/h;
        elif k==n-2:
            f[k]=(-2.0*v[k-5]+15.0*v[k-4]-50.0*v[k-3]+100.0*v[k-2]-150.0*v[k-1]+77.0*v[k]+10.0*v[k+1])/60.0/h;
        else:
            f[k]=(10.0*v[k-6]-72.0*v[k-5]+225.0*v[k-4]-400.0*v[k-3]+450.0*v[k-2]-360.0*v[k-1]+147.0*v[k])/60.0/h;
    return f


#~ A derivative by 4 datapoints
def dervec4(v,h=1):
    global f,k
    # Finds a derivative by 4 points
    # v - the function to derivate
    # h - step size

    n=len(v);
    f=zeros(n)
    for k in range(n):
        if k==0:
            f[0]=(-11.0*v[0]+18.0*v[1]-9.0*v[2]+2.0*v[3])/6.0/h ;
        elif k==1:
            f[1]=(-2.0*v[0]-3.0*v[1]+6.0*v[2]-v[3])/6.0/h ;
        elif k>1 and k<n-1:
            f[k]=(v[k-2]-6.0*v[k-1]+3.0*v[k]+2.0*v[k+1])/6.0/h ;
        else:
            f[k]=(-2*v[k-3]+9.0*v[k-2]-18.0*v[k-1]+11.0*v[k])/6.0/h;
    return f


#~ A derivative by 3 datapoints
def dervec3(v,h=1):
    global f
    # Finds a derivative by 3 points
    # v - the function to derivate
    # h - step size
    n=len(v);
    f=zeros(n)
    for k in range(n):
        if k==0:
            f[0]=(-3.0*v[0]+4.0*v[1]-v[2])/2.0/h ;
        elif k>0 and k<n-1:
            f[k]=(v[k+1]-v[k-1])/2.0/h ;
        else:
            f[k]=(v[k-2]-4.0*v[k-1]+3.0*v[k])/2.0/h ;
    return f


def findmin(F, Rstar_range):
    # ruturns the position of minimum of F as function of R
    DF=dervec3(F)
    if sum(sign(DF)) == -len(DF):
        R0 = Rstar_range[-1]
    elif sum(sign(DF)) == len(DF):
        R0 = Rstar_range[0]
    else:
        nearest_to_zero_positive_index = find(sign(DF) ==  1)[ 0]
        nearest_to_zero_negative_index = find(sign(DF) == -1)[-1]
        R1 = Rstar_range[nearest_to_zero_positive_index];R1=float(R1)
        R2 = Rstar_range[nearest_to_zero_negative_index];R2=float(R2)
        DF1 = DF[nearest_to_zero_positive_index];DF1=float(DF1)
        DF2 = DF[nearest_to_zero_negative_index];DF2=float(DF2)
        R0 = -DF1/(DF2-DF1)*(R2-R1)+R1
    return R0

def findzero(F, R):
    nearest_to_zero_positive_index = np.abs(np.diff(np.sign(F))).argmax()
    nearest_to_zero_negative_index = nearest_to_zero_positive_index+1
    R1 = R[nearest_to_zero_positive_index];R1=float(R1)
    R2 = R[nearest_to_zero_negative_index];R2=float(R2)
    F1 = F[nearest_to_zero_positive_index];F1=float(F1)
    F2 = F[nearest_to_zero_negative_index];F2=float(F2)
    R0 = -F1/(F2-F1)*(R2-R1)+R1
    return R0

def findmin7(F, Rstar_range):
    # ruturns the position of minimum of F as function of R
    DF=dervec7(F)
    if sum(sign(DF)) == -len(DF):
        R0 = Rstar_range[-1]
    elif sum(sign(DF)) == len(DF):
        R0 = Rstar_range[0]
    else:
        i = 0
        while sign(DF[i]) ==  -1:
            index = i
            i = i+1
        nearest_to_zero_positive_index = i
        nearest_to_zero_negative_index = i-1
        R1 = Rstar_range[nearest_to_zero_positive_index];R1=float(R1)
        R2 = Rstar_range[nearest_to_zero_negative_index];R2=float(R2)
        DF1 = DF[nearest_to_zero_positive_index];DF1=float(DF1)
        DF2 = DF[nearest_to_zero_negative_index];DF2=float(DF2)
        R0 = -DF1/(DF2-DF1)*(R2-R1)+R1
    return R0

def mplot(x=[],y=[],xname = 'x', yname = 'y', xlog = False, ylog = False, color = 'black', PlotLine = True, marker = 'circle', markersize = '2pt', title='notitle', label = ''):
    fig = plt.figure()
    if x == []:
        x = range(len(y))
    if len(x) == 2:
        X = x[0]
        Xerr = x[1]
    else:
        X = x
        Xerr = np.zeros(len(X))
    if len(y) == 2:
        Y = y[0]
        Yerr = y[1]
    else:
        Y = y
        Yerr = np.zeros(len(Y))
    plt.errorbar(X, Y, xerr=Xerr, yerr=Yerr, linestyle=':',marker='o', label=label, color=color)
#~ Makes xy plot, xname and yname are the names of axis



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


def progressBar(value, endvalue, bar_length=20, text = ''):

    percent = float(value) / endvalue
    arrow = '-' * int(round(percent * bar_length)-1) + '>'
    spaces = ' ' * (bar_length - len(arrow))

    sys.stdout.write('\ralpha = {:06.2f}'.format(value)+" Percent: [{0}] {1}%".format(arrow + spaces, int(round(percent * 100)))+' '+text)
    #~ sys.stdout.write('\ralpha = {:.3f}".format(value))
    sys.stdout.flush()






def file2dic(fname):
    text = open(fname,'r').read()
    content = text.split('\n')
    content.remove('')
    header = content[0]

    header = header.split('\t')
    header.remove('')
    dic = {}
    for key in header: dic[key] = []
    for i in range(1,len (content)):
        string = content[i]
        string = string.split('\t')
        for j in range(len(header)):
            key = header[j]
            dic[key].append(string[j])

    return dic


def dic2file(dic, fname):

    header = ''
    values = ''
    datasize = len(dic.values()[0])

    for key in dic.keys():
        header += key+'\t'
    header += '\n'
    outfile = open(fname, 'w')
    outfile.write(header)
    try:
        for i in range(datasize):
            values = ''
            for key in dic.keys():
                values += str(dic[key][i])+'\t'
            values += '\n'
            #print (values)
            outfile.write(values)
    except TypeError:
        for key in dic.keys():
            values += str(output[key])+'\t'
        values += '\n'
        outfile.write(values)
    outfile.close()

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

def next_pow_two(n):
    i = 1
    while i < n:
        i = i << 1
    return i
def autocorr_func_1d(x, norm=True):
    x = np.atleast_1d(x)
    if len(x.shape) != 1:
        raise ValueError("invalid dimensions for 1D autocorrelation function")
    n = next_pow_two(len(x))

    # Compute the FFT and then (from that) the auto-correlation function
    f = np.fft.fft(x - np.mean(x), n=2*n)
    acf = np.fft.ifft(f * np.conjugate(f))[:len(x)].real
    acf /= 4*n

    # Optionally normalize
    if norm:
        acf /= acf[0]

    return acf
def estimated_autocorrelation(x):
    n = len(x)
    variance = x.var()
    x = x-x.mean()
    # ~ r = N.correlate(x, x, mode = 'full')
    r = N.correlate(x, x, mode = 'same')
    result = r/(variance*n)
    return result


def autocorr(x):
    n = x.size
    norm = (x - np.mean(x))
    result = np.correlate(norm, norm, mode='same')
    acorr = result[n//2 + 1:] / (x.var() * np.arange(n-1, n//2, -1))
    lag = np.abs(acorr).argmax() + 1
    r = acorr[lag-1]
    if np.abs(r) > 0.5:
      print('Appears to be autocorrelated with r = {}, lag = {}'. format(r, lag))
    else:
      print('Appears to be not autocorrelated')
    return r, lag

def htmlcolor(r, g, b):
    def _chkarg(a):
        if isinstance(a, int): # clamp to range 0--255
            if a < 0:
                a = 0
            elif a > 255:
                a = 255
        elif isinstance(a, float): # clamp to range 0.0--1.0 and convert to integer 0--255
            if a < 0.0:
                a = 0
            elif a > 1.0:
                a = 255
            else:
                a = int(round(a*255))
        else:
            raise ValueError('Arguments must be integers or floats.')
        return a
    r = _chkarg(r)
    g = _chkarg(g)
    b = _chkarg(b)
    return '#{:02x}{:02x}{:02x}'.format(r,g,b)


def get_N_HexCol(N=5):
    import colorsys
    nums = np.linspace(0,255, N, dtype = int)

    hex_out = []
    for num in nums :
        #~ print (color)
        hex_out.append(htmlcolor(int(num), 100, 0))

    return hex_out










def pearson(X, Y):
    global MX, MY, MXY
    MX = np.mean(X);
    DX = np.std(X)

    MY = np.mean(Y);
    DY = np.std(Y)

    # ~ COV = np.mean((X-MX)*(Y-MY))
    COV = np.mean(X*Y) - MX*MY
    if not DX or not DY or not COV:
       K = 1
       return K
    K = COV/DX/DY
    return K

def autopearson(X,t):
    global MX, MY, MXY
    MX = np.mean(X);
    DX = np.std(X)
    Y = np.concatenate((X[t:],X[:t]))
    COV = np.mean(X*Y) - MX**2
    if (DX<1e-10) or (np.abs(COV)<1e-10):
       K = 1
       return K
    K = COV/DX**2
    return K




def acf(X):
    a = np.ones(len(X))
    for t in range(len(X)):
        a[t] = autopearson(X,t)
    return a





############ Colors ####################################################
def get_colors_poster():
    pK_range = [-np.infty, 6.,7.,8.]
    cs_range = [0., 0.006, 0.15, 0.4,] # mol/l

    colors = {}

    colors[(0, np.infty)] = '#c8c8c8ff'
    colors[(0.006, np.infty)] = '#7d7d7dff'
    colors[(0.15, np.infty)] = '#4c4a4bff'
    colors[(0.4, np.infty)] = '#292728ff'

    colors[(0, 6.)] = '#c9efa1ff'
    colors[(0.006, 6.)] = '#80d624ff'
    colors[(0.15, 6.)] = '#4d8016ff'
    colors[(0.4, 6.)] = '#29440cff'

    colors[(0, 5.)] = '#000000'
    colors[(0.006, 5.)] = '#000000'
    colors[(0.15, 5.)] = '#000000'
    colors[(0.4, 5.)] = '#000000'

    colors[(0, 8.)] = '#000000'
    colors[(0.006, 8.)] = '#000000'
    colors[(0.15, 8.)] = '#000000'
    colors[(0.4, 8.)] = '#000000'

    colors[(0, 7.)] = '#a1efeeff'
    colors[(0.006, 7.)] = '#24d6d4ff'
    colors[(0.15, 7.)] = '#16807fff'
    colors[(0.4, 7.)] = '#0c4444ff'

    colors[(0, -np.infty)] = '#efa1baff'
    colors[(0.006, -np.infty)] = '#d6245eff'
    colors[(0.15, -np.infty)] = '#801638ff'
    colors[(0.4, -np.infty)] = '#440c1eff'


    colors[(1e-07, 7.0)] = '#440c1eff'




    return colors
def get_colors():
    pK_range = [-np.infty, 3.,5.,7.]
    cs_range = [0.006, 0.15] # mol/l
    colors = {}

    color_scheme = ['#181818', '#639bbe', '#e75621', '#f5a601',
                    '#cc8f91', '#ab8fcc', '#8fccca', '#a8c784',
                    '#c22326', '#61c742', '#fdb632', '#027878',
                    '#801638', '#588726', '#268786', '#552687',]


    colors[(0.006, 3.)] = '#ff6969ff'
    colors[(0.15, 3.)] = '#ff6969ff'
    #colors[(0.15, 3.)] = '#f00000ff'
    colors[(0.4, 3.)] = '#8c0000ff'
    colors[(0.006, 5.)] = '#69ff69ff'
    colors[(0.15, 5.)] = '#69ff69ff'
    #colors[(0.15, 5.)] = '#00f000ff'
    colors[(0.4, 5.)] = '#008c00ff'
    colors[(0.006, 7.)] = '#6868ffff'
    colors[(0.15, 7.)] = '#6868ffff'
    #colors[(0.15, 7.)] = '#0000f0ff'
    colors[(0.4, 7.)] = '#00008cff'

    return colors
colors = get_colors()





def getData2Plot(GG):

    P_arr = []
    PA_arr = []
    NNa_arr = []
    NCl_arr = []
    RR = []
    V_arr = []
    DICT = {}

    rand_g = np.random.choice(GG)
    bulk = rand_g.getbulk()
    for g in GG:
        try:
            P = (g.Means['pressure'] - rand_g.Posm) *g.punit/1e5
            P_err = g.Erros['pressure']        *g.punit/1e5
            P_arr.append([P, P_err])
        except KeyError:
            pass
        RR.append(g.box_l)
        V_arr.append(g.box_l**3)


        try:
            PA_arr.append([g.Means['PA'], g.Erros['PA']])
        except (KeyError):
            if g.p['K'] == -np.infty:
                PA_arr.append([g.MPC*16, 0])
            elif g.p['K'] == np.infty:
                PA_arr.append([0, 0])
            else:
                print ('Warning: g.Means[\'PA\'] is not there for unknown reason')
        try:
            NNa_arr.append([g.Means['Na'], g.Erros['Na']])
            NCl_arr.append([g.Means['Cl'], g.Erros['Cl']])
        except (KeyError):
            NNa_arr.append([0, 0])
            NCl_arr.append([0, 0])
    DICT = {
        'P_arr': np.array(P_arr).T,
        'PA_arr': np.array(PA_arr).T,
        'NNa_arr': np.array(NNa_arr).T,
        'NCl_arr': np.array(NCl_arr).T,
        'RR': np.array(RR).T,
        'V_arr': np.array(V_arr).T,
    }

    return DICT



fig_alpha = None
fig_alphaP = None
fig_PV = None
fig_N = None
fig_NNa = None
fig_NCl = None
fig_NCa = None
figs = [fig_PV, fig_alpha, fig_NNa, fig_NCl, fig_NCa]



def plotP(GG, label, title, color='black', fig = fig_PV):

    [Req, Peq, R10, P10, ] = getR_eq(GG)
    # def vplot(x=[],y=[], xname = 'x', yname = 'y', xlog = False, ylog = False, color = 'black', PlotLine = True, marker = 'circle', markersize = '2pt', title='notitle'):

    # These three lines plot the circle indicating the place where Pressure is zero
    # ~ fig = vplot([R_eq], [P_eq], xname = 'Req'+str(GG[0]), yname = 'Peq'+str(GG[0]), color=color, marker= 'circle', markersize = '4pt', g = fig)
    fig = vplot([1/Veq], [Peq], xname = 'Req'+str(GG[0]), yname = 'Peq'+str(GG[0]), color=color, marker= 'circle', markersize = '4pt', g = fig)
    fig = vplot([1/V10], [P10], xname = 'R10'+str(GG[0]), yname = 'P10'+str(GG[0]), color=color, marker= 'circle', markersize = '4pt', g = fig)
    xy.MarkerLine.color.val = color
    xy.MarkerLine.width.val = '1pt'
    xy.MarkerFill.color.val = 'white'

    dname = GG[0].name.replace('box_l'+str(GG[0].box_l)+'_','').replace('_N'+str(GG[0].N_Samples), '')
    # ~ fig = vplot(RR, P_arr, xname = 'R'+str(GG[0]), yname = 'P'+str(GG[0]), color=color, style = 'dotted', g = fig, keylabel=label)
    #fig = vplot(RR, P_arr, xname = 'R'+dname, yname = 'P'+dname, color=color, style = 'dotted', g = fig, keylabel=label)
    fig = vplot(1/VV, P_arr, xname = 'R'+dname, yname = 'P'+dname, color=color, style = 'dotted', g = fig, keylabel=label)
    fig.Root.notes.val = 'gel_pressure'
    page = fig.Root.page1
    graph = page.graph1

    # ~ xy.PlotLine.width.val = '4pt'
    # ~ graph.x.min.val = 1
    graph.y.min.val = -10
    graph.y.max.val = 30
    graph.x.max.val = 3
    graph.x.min.val = 'auto'
    graph.x.log.val = False
    fig.Root.notes.val += '_log'*graph.x.log.val
    page.width.val = str(figsize)+'cm'
    page.height.val = str(figsize / aspect)+'cm'

    # ~ pagePV.width.val = width
    # ~ pagePV.height.val = height
    if GG[0].p['Ca'] != np.infty and GG[0].lB != 0.:
        # ~ graph.x.min.val = 1
        graph.y.min.val = -30
        graph.y.max.val = 10
        graph.x.max.val = 20

    # ~ graph.x.label.val = 'box length, \sigma'
    #graph.x.label.val = 'V, l/mol'
    graph.x.label.val = 'gel density, \\phi, mol/l'
    graph.y.label.val = 'P - P_{osm}, bar'



    ################## Plot the acf for random gel ########################
    # ~ rand_g = np.random.choice(GG)
    P4acf = (rand_g.Samples['pressure'][:,0] - rand_g.Posm) * rand_g.punit/1e5

    if 'Re00' in rand_g.keys['md']:
        Re4acf = rand_g.Samples['Re00'][:,0]

    #The following two strings are added to let the old autocorrelation estimation work
    if 'Re' in rand_g.keys['md']:
        Re4acf = rand_g.Samples['Re'][:,0]

    ACF_P = autocorrelation(P4acf)[0]
    ACF_Re = autocorrelation(Re4acf)[0]
    fig.SetData('ACF_P_y'+str(rand_g), ACF_P)
    fig.SetData('ACF_P_x'+str(rand_g), range(len(ACF_P)))
    fig.SetData('ACF_Re_y'+str(rand_g), ACF_Re)
    fig.SetData('ACF_Re_x'+str(rand_g), range(len(ACF_Re)))

    page_acf = fig.Root.Add('page')
    graph_acf = page_acf.Add('graph')
    graph_acf.Add('key')
    addxy(graph_acf,
            x_dataname='ACF_P_x'+str(rand_g),
            y_dataname='ACF_P_y'+str(rand_g),
            marker='cross',
            markersize='2pt', color = color, keylabel = 'Re', xname='Samples', yname='ACF')
    addxy(graph_acf,
            x_dataname='ACF_Re_x'+str(rand_g),
            y_dataname='ACF_Re_y'+str(rand_g),
            marker='circle', markersize='2pt', color = 'black', keylabel = 'P', xname='Samples', yname='ACF')
    label = graph_acf.Add('label')
    label.label.val = str(rand_g).replace('_','\_')


    ################## Plot the acf for random gel ########################



    return fig




    # ~ ax_PV.axis(xmax = max(RR), xmin = min(RR))
    # ~ ax_PV.legend()

def alphaDonnan_old(cp, cs, pH, pK):
    global ROOTS, eq, alpha, a1,a2,a3,a4
    print (cp, cs, pH, pK)
    aleph = 10**(pK-pH)

    a1=-cp/cs
    a2=cp/cs + aleph - 1/aleph
    a3=2/aleph
    a4=-1/aleph
    p=[a1,a2,a3,a4]
    ROOTS = np.roots(p)
    #~ print '###########'
    #print (ROOTS)
    try:
        alpha = float(ROOTS[find((ROOTS>0)*(ROOTS<1))])
    except TypeError:
        print ('warning: alpha has two roots in (0,1) interval')
        alpha = ROOTS[find((ROOTS>0)*(ROOTS<1))][0]

    #~ print 'alpha = ',alpha
    return alpha

from scipy.optimize import root



def alphaDonnan(cp:float, cs:float, pH:float, pK:float, ksi:float, alpha_init:float =0.05):
    '''
    Inputs:
      cs         -- salt concentration    [mol/l]
      cp         -- polymer concentration [mol/l]
      pH         -- acidity of the bath
      pK         -- polymer characteristic
      ksi        -- 2 * c(Ca) / c(Na)
      alpha_init -- initial value
    ###
    Output:
      alpha      -- solution
      lam        -- solution
    '''

    
    unit_of_length = 0.7       # nm
    Navogadro      = 6.022e23  # 1/mol
    unit           = Navogadro*1000*(unit_of_length*1e-9)**3  # l/mol
    #print(f"""
    #     Donnan (Num) Provided: salt concentration: {cs} [mol/l] | {cs*unit} [unitless]
    #     polymer concentration: {cp} [mol/l] | {cp*unit} [unitless]
    #     pH: {pH}
    #     pK: {pK}
    #      (init) alpha: {alpha_init}
    #      """)
    cs = cs*unit   # mol/L / L/mol -> [unitless]
    cp = cp*unit   # mol/L / L/mol -> [unitless]
    tol = 1e-7

    alpha_b = (1+10**(pK-pH))**-1
    def f1(alpha):
        a1 = 1
        a2 = alpha * cp / cs
        a3 = -1/(1+ksi)
        a4 = -ksi/(1+ksi)
        p  = [a1, a2, a3, a4]
        lam = np.roots(p)
        res = lam[0.0<lam]
        if len(res) == 1: lam = np.real(res[0])
        else: 
            #print("Solution is: ", res); 
            lam = None
        return lam

    def f2(alpha, lam):
        equation2 = lam - alpha*(1-alpha_b)/(1-alpha)/alpha_b  # alpha
        return equation2

    should_solve = True
    while should_solve:
        lam = f1(alpha_init)
        res = root(f2, x0=(alpha_init), args=(lam))
        if abs(alpha_init - res['x']) < tol: should_solve = False
        alpha_init = res['x']
    return res['x'][0]


def alphaBulk(pH, pK):

    alpha_bulk = 10**(pH-pK)/(1+10**(pH-pK))
    return alpha_bulk


def getR_eq(GG):
    global PP, NNA, NNna, NNcl, NNca, alphaDonnan_arr, alpha_bulk, RR, VV, rand_g
    NNna = []
    NNcl = []
    NNca = []

    NNA = []
    PP  = []
    alphaDonnan_arr = []

    RR = []
    rand_g = np.random.choice(GG)
    bulk = rand_g.getbulk()
    rand_g.Posm = bulk.Means['pressure']
    for g in GG:
        P = (g.Means['pressure'] - rand_g.Posm) * g.punit/1e5
        P_err = g.Erros['pressure']             * g.punit/1e5
        PP.append([P, P_err])

        RR.append(g.box_l)

        NNA.append([g.Means['PA'], g.Erros['PA']])
        NNna.append([g.Means['Na'], g.Erros['Na']])
        NNcl.append([g.Means['Cl'], g.Erros['Cl']])
        try: NNca.append([g.Means['Ca'], g.Erros['Ca']])
        except KeyError: pass

        cs = bulk.Means['Na'] / bulk.box_l**3 # !important. For multivalent ions here must be an ionic strength
        if rand_g.p['Ca']**-1:
            #cs = 0.5*(bulk.Means['Na'] + bulk.Means['Cl']+ 2**2 * bulk.Means['Ca']) / bulk.box_l**3
            cs = bulk.Means['Cl'] / bulk.box_l**3
            ksi = 2*bulk.Means['Ca'] / bulk.Means['Na']
        else: ksi = 0.
        cp = g.MPC*16 / g.box_l**3 #The number of ionogenic groups (the nodes are excluded)
        alphaDonnan_arr.append(alphaDonnan(cp, cs, g.p['H'], g.p['K'], ksi=ksi))
    alpha_bulk = alphaBulk(g.p['H'], g.p['K'])



    RR   = np.array(RR)
    PP   = np.array(PP).T
    NNA  = np.array(NNA).T
    NNna  = np.array(NNna).T
    NNcl  = np.array(NNcl).T
    NNca  = np.array(NNca).T

    idx00 = (abs(PP[0]   ) == min(abs(PP[0]   ))).argmax()
    idx10 = (abs(PP[0]-10) == min(abs(PP[0]-10))).argmax()
    idx30 = (abs(PP[0]-30) == min(abs(PP[0]-30))).argmax()


    bulk = rand_g.getbulk()
    bulk.Pearson(keys = bulk.keys['md']+bulk.keys['re'])

    N = (rand_g.MPC*16+8)

    Vbox = RR[idx00]**3
    VV = RR**3
    NNna_out_arr = (Vbox - VV) * bulk.Means['Na'] / bulk.box_l**3
    NNna_out_err = (Vbox - VV) * bulk.Erros['Na'] / bulk.box_l**3
    NNcl_out_arr = (Vbox - VV) * bulk.Means['Cl'] / bulk.box_l**3
    NNcl_out_err = (Vbox - VV) * bulk.Erros['Cl'] / bulk.box_l**3


    NNna_out_arr = np.array([NNna_out_arr, NNna_out_err])
    NNcl_out_arr = np.array([NNcl_out_arr, NNcl_out_err])

    NNna = NNna + NNna_out_arr
    NNcl = NNcl + NNcl_out_arr

    NNna[0]  -= NNna[0][idx00]
    NNna /= (rand_g.MPC*16+8)
    NNcl[0]  -= NNcl[0][idx00]
    NNcl /= (rand_g.MPC*16+8)


    try:
        NNca_out_arr = (Vbox - VV) * bulk.Means['Ca'] / bulk.box_l**3
        NNca_out_err = (Vbox - VV) * bulk.Erros['Ca'] / bulk.box_l**3
        NNca_out_arr = np.array([NNca_out_arr, NNca_out_err])

        NNca = NNca + NNca_out_arr


        NNca[0]  -= NNca[0][idx00]
        NNca /= (rand_g.MPC*16+8)


    except KeyError: pass


    VV = VV * rand_g.unit / N #sigma**3

    return [idx00, idx10, idx30]



def langevin(x):
    return np.cosh(x)/np.sinh(x) - 1./x
def invlangevin(y):
    def func(x):
        return y - langevin(x)

    x = float(fsolve(func,1))
    return x



def getidx00(GG):
    PP  = []
    RR = []
    for g in GG:
        P =     g.Means['pressure'] * g.punit/1e5
        PP.append(P)
        #PP_flory.append(g.mean_field_pressure(interaction = 'flory') * g.punit/1e5)
        RR.append(g.box_l)
    RR   = np.array(RR)
    PP   = np.array(PP)
    #PP_mf = np.array(PP_mf) - 7
    idx00 = (abs(PP) == min(abs(PP))).argmax()
    return idx00


def plot_combgel(GG, label, color='black', fig_PV = fig_PV, vs_volume = False):
    global idx00
    PP  = []
    #PP_flory  = []
    PP_virial  = []
    RR = []
    rand_g = np.random.choice(GG)

    for g in GG:
        P =     g.Means['pressure'] * g.punit/1e5
        P_err = g.Erros['pressure'] * g.punit/1e5
        g.P = [P, P_err]
        PP.append([P, P_err])
        #PP_flory.append(g.mean_field_pressure(interaction = 'flory') * g.punit/1e5)
        #PP_virial.append(g.mean_field_pressure(interaction = 'virial') * g.punit/1e5)
        RR.append(g.box_l)

    RR   = np.array(RR)
    PP   = np.array(PP).T
    #PP_mf = np.array(PP_mf) - 7
    idx00 = (abs(PP[0]   ) == min(abs(PP[0]   ))).argmax()
    idx10 = (abs(PP[0]-10) == min(abs(PP[0]-10))).argmax()
    idx30 = (abs(PP[0]-30) == min(abs(PP[0]-30))).argmax()


    bulk = rand_g.getbulk()
    N = (rand_g.MPC*16+8)

    Vbox = RR[idx00]**3
    VV = RR**3

    A = 3*3**0.5/4 # A is the coeffitient for diamond lattice Re = (A*V) ** (1./3)
    R00 = (VV[idx00]/16*A)**(1./3)
    R10 = (VV[idx10]/16*A)**(1./3)
    R30 = (VV[idx30]/16*A)**(1./3)
    RR = (VV/16*A)**(1./3)

    VV = VV * rand_g.unit / N #sigma**3


    P00 = PP[0][idx00]
    P10 = PP[0][idx10]
    P30 = PP[0][idx30]
    V00 = VV[idx00]
    V10 = VV[idx10]
    V30 = VV[idx30]
    #R00 = RR[idx00]
    #R10 = RR[idx10]
    #R30 = RR[idx30]
    X00 = R00
    X10 = R10
    X30 = R30
    XX  = RR

    if vs_volume:
        X00 = V00
        X10 = V10
        X30 = V30
        XX  = VV


    dname = GG[0].name.replace('box_l'+str(GG[0].box_l)+'_','').replace('_N'+str(GG[0].N_Samples), '')
    #fig_PV = vplot([X00], [P00], xname = 'V00'+str(GG[0]), yname = 'P00'+str(GG[0]), color=color, marker= 'circle', markersize = '4pt', g = fig_PV)
    #xy.MarkerLine.color.val = xy.MarkerFill.color.val;xy.MarkerFill.color.val = 'white'; xy.MarkerLine.width.val = '1.0pt'
    fig_PV = vplot([X10], [P10], xname = 'V10'+str(GG[0]), yname = 'P10'+str(GG[0]), color=color, marker= 'cross', markersize = '4pt', g = fig_PV)
    #xy.MarkerLine.color.val = xy.MarkerFill.color.val;xy.MarkerFill.color.val = 'white'; xy.MarkerLine.width.val = '1.0pt'
    fig_PV = vplot([X30], [P30], xname = 'V30'+str(GG[0]), yname = 'P30'+str(GG[0]), color=color, marker= 'square', markersize = '4pt', g = fig_PV)
    #xy.MarkerLine.color.val = xy.MarkerFill.color.val;xy.MarkerFill.color.val = 'white'; xy.MarkerLine.width.val = '1.0pt'
    fig_PV = vplot( XX,    PP,   xname = 'V'+dname, yname = 'P'+dname, color=color, style = 'solid', g = fig_PV, keylabel=label)
    #fig_PV = vplot( RR,    PP_flory,   xname = 'V'+dname, yname = 'P_flory'+dname, keylabel = 'flory', color=color, style = 'dotted', marker = 'none', markersize = '4pt', g = fig_PV, )
    #fig_PV = vplot( RR,    PP_virial,   xname = 'V'+dname, yname = 'P_virial'+dname, keylabel = 'virial', color=color, style = 'dashed', marker = 'none', markersize = '4pt', g = fig_PV, )
    graph_PV = fig_PV.Root.page1.graph1

    # C-axis a common
    x = graph_PV.x
    x.max.val = 100.
    x.min.val = 0.1
    x.log.val = False

    #xlabel = 'volume'
    #x.label.val = 'gel molar volume, V, l/mol'
    #xlabel = 'density'
    #x.label.val = 'gel density, \\phi, mol/l'
    xlabel = 'extension'
    x.label.val = 'R, \\sigma'
    if vs_volume: x.label.val = 'V, l/mol'


    fig_PV.Root.notes.val = 'gel_pressure'+'_log'*x.log.val +'_'+xlabel

    graph_PV.y.min.val = -10
    graph_PV.y.max.val = 31
    graph_PV.y.label.val = 'P, bar'


    return fig_PV

def plot_all(GG, label, title, color='black', figs = figs, vs='density', \
                MarkerLine = 'black', MarkerFill = 'white', MarkerSize = '2pt', PlotLineWidth = '1pt', PlotLineStyle='solid'):
    [fig_PV, fig_alpha, fig_NNa, fig_NCl, fig_NCa] = figs

    [idx00, idx10, idx30] = getR_eq(GG)

    P00 = PP[0][idx00]
    P10 = PP[0][idx10]
    P30 = PP[0][idx30]
    V00 = VV[idx00]
    V10 = VV[idx10]
    V30 = VV[idx30]
    NA00 = NNA[0][idx00]
    NA10 = NNA[0][idx10]
    NA30 = NNA[0][idx30]


    if vs == 'density': vs_ = -1;
    else: vs_ = 1
    dname = GG[0].name.replace('box_l'+str(GG[0].box_l)+'_','').replace('_N'+str(GG[0].N_Samples), '')

    fig_PV = vplot([V00**vs_], [P00], xname = 'V00'+str(GG[0]), yname = 'P00'+str(GG[0]), color=color, marker= 'circle', markersize = '6pt', g = fig_PV)
    xy.MarkerLine.color.val = MarkerLine; xy.MarkerFill.color.val = MarkerFill; xy.MarkerLine.width.val = '0.5pt'

    fig_PV = vplot([V10**vs_], [P10], xname = 'V10'+str(GG[0]), yname = 'P10'+str(GG[0]), color=color, marker= 'cross', markersize = '6pt', g = fig_PV)
    xy.MarkerLine.color.val = MarkerLine; xy.MarkerFill.color.val = MarkerFill; xy.MarkerLine.width.val = '0.5pt'

    fig_PV = vplot([V30**vs_], [P30], xname = 'V30'+str(GG[0]), yname = 'P30'+str(GG[0]), color=color, marker= 'square', markersize = '6pt', g = fig_PV)
    xy.MarkerLine.color.val = MarkerLine; xy.MarkerFill.color.val = MarkerFill; xy.MarkerLine.width.val = '0.5pt'

    fig_PV = vplot( VV**vs_,    PP,   xname = 'V'+dname, yname = 'P'+dname, color=color, style = 'solid', markersize = MarkerSize, g = fig_PV, keylabel=label)
    xy.MarkerLine.color.val = MarkerLine; xy.MarkerFill.color.val = MarkerFill; xy.MarkerLine.width.val = '0.5pt';
    xy.PlotLine.bezierJoin.val = True; xy.PlotLine.width.val = PlotLineWidth; xy.PlotLine.style.val = PlotLineStyle
    graph_PV = fig_PV.Root.page1.graph1

    # C-axis a common
    x = graph_PV.x
    x.max.val = max(0.1**vs_, 10**vs_)
    x.min.val = min(0.1**vs_, 10**vs_)
    x.log.val = True

    xlabel = vs
    if vs == 'volume':
        x.label.val = 'gel molar volume, V, l/mol'
    elif vs == 'density':
        x.label.val = 'hydrogel density, \\varphi, [mol/l]'
    else: pass


    fig_PV.Root.notes.val = 'gel_pressure'+'_log'*x.log.val +'_'+xlabel

    graph_PV.y.min.val = -10
    graph_PV.y.max.val = 31
    graph_PV.y.label.val = '\Delta P, [bar]'

    fig_alpha = vplot([V00**vs_], [NA00/rand_g.MPC/16], xname = 'V00_'+dname, yname = 'alpha00_'+dname,color=color, marker= 'circle', markersize = '6pt', g = fig_alpha)
    xy.MarkerLine.color.val = MarkerLine; xy.MarkerFill.color.val = MarkerFill; xy.MarkerLine.width.val = '0.5pt'
    
    fig_alpha = vplot([V10**vs_], [NA10/rand_g.MPC/16], xname = 'V10_'+dname, yname = 'alpha10_'+dname,color=color, marker= 'cross', markersize = '6pt', g = fig_alpha)
    xy.MarkerLine.color.val = MarkerLine; xy.MarkerFill.color.val = MarkerFill; xy.MarkerLine.width.val = '0.5pt'
    
    fig_alpha = vplot([V30**vs_], [NA30/rand_g.MPC/16], xname = 'V30_'+dname, yname = 'alpha30_'+dname,color=color, marker= 'square', markersize = '6pt', g = fig_alpha)
    xy.MarkerLine.color.val = MarkerLine; xy.MarkerFill.color.val = MarkerFill; xy.MarkerLine.width.val = '0.5pt'
    
    fig_alpha = vplot( VV**vs_,    NNA/rand_g.MPC/16,   xname = 'V_'+dname,   yname = 'alpha_'+dname,  color=color, style = 'solid', markersize = MarkerSize, g = fig_alpha, keylabel=label)
    xy.MarkerLine.color.val = MarkerLine; xy.MarkerFill.color.val = MarkerFill; xy.MarkerLine.width.val = '0.5pt'
    xy.PlotLine.bezierJoin.val = True; xy.PlotLine.width.val = PlotLineWidth; xy.PlotLine.style.val = PlotLineStyle    
    
    fig_alpha = vplot( VV**vs_,    alphaDonnan_arr,     xname = 'V_'+dname,   yname = 'alphaDonnan_'+dname,color=color, marker='none', style = 'dashed', g = fig_alpha)
    fig_alpha = vplot( np.array([1e-3,1e3])**vs_,[alpha_bulk,alpha_bulk],     xname = 'V2_'+dname,   yname = 'alphaBulk_'+dname,color=color, marker='none', style = 'dotted', g = fig_alpha)
    xy.PlotLine.width.val = '1pt'; xy.PlotLine.style.val = 'solid'

    graph_alpha = fig_alpha.Root.page1.graph1
    for i in ['max', 'min', 'log', 'label']:
        exec('graph_alpha.x.'+i+'.val = x.'+i+'.val')
    graph_alpha.y.min.val = 0
    graph_alpha.y.max.val = 1.05
    graph_alpha.y.label.val = '\\alpha'
    fig_alpha.Root.notes.val = 'gel_alpha'+'_log' * x.log.val +'_'+xlabel

    fig_NNa = vplot([V00**vs_], [NNna[0][idx00]], xname = 'Veq_'+dname, yname = 'N00_na_'+dname,color=color, marker= 'circle', markersize = '6pt', g = fig_NNa)
    xy.MarkerLine.color.val = MarkerLine; xy.MarkerFill.color.val = MarkerFill; xy.MarkerLine.width.val = '0.5pt'    

    fig_NNa = vplot([V10**vs_], [NNna[0][idx10]], xname = 'V10_'+dname, yname = 'N10_na_'+dname,color=color, marker= 'cross', markersize = '6pt', g = fig_NNa)
    xy.MarkerLine.color.val = MarkerLine; xy.MarkerFill.color.val = MarkerFill; xy.MarkerLine.width.val = '0.5pt'

    fig_NNa = vplot([V30**vs_], [NNna[0][idx30]], xname = 'V30_'+dname, yname = 'N30_na_'+dname,color=color, marker= 'square', markersize = '6pt', g = fig_NNa)
    xy.MarkerLine.color.val = MarkerLine; xy.MarkerFill.color.val = MarkerFill; xy.MarkerLine.width.val = '0.5pt'

    fig_NNa = vplot( VV**vs_,    NNna,            xname = 'V_'+dname,   yname = 'N_na_'+dname,  color=color, style = 'solid', markersize = MarkerSize, g = fig_NNa, keylabel=label)
    xy.MarkerLine.color.val = MarkerLine; xy.MarkerFill.color.val = MarkerFill; xy.MarkerLine.width.val = '0.5pt'
    xy.PlotLine.bezierJoin.val = True; xy.PlotLine.width.val = PlotLineWidth; xy.PlotLine.style.val = PlotLineStyle
    
    fig_NNa.Root.notes.val = 'gel_Na'+'_log' * x.log.val +'_'+xlabel
    graph_NNa = fig_NNa.Root.page1.graph1
    for i in ['max', 'min', 'log', 'label']:
        exec('graph_NNa.x.'+i+'.val = x.'+i+'.val')
    graph_NNa.y.label.val = '\\Delta N_{Na}/N_{gel}'

    fig_NCl = vplot([V00**vs_], [NNcl[0][idx00]], xname = 'Veq_'+dname, yname = 'N00_cl_'+dname,color=color, marker= 'circle', markersize = '6pt', g = fig_NCl)
    xy.MarkerLine.color.val = MarkerLine; xy.MarkerFill.color.val = MarkerFill; xy.MarkerLine.width.val = '0.5pt'
    
    fig_NCl = vplot([V10**vs_], [NNcl[0][idx10]], xname = 'V10_'+dname, yname = 'N10_cl_'+dname,color=color, marker= 'cross', markersize = '6pt', g = fig_NCl)
    xy.MarkerLine.color.val = MarkerLine; xy.MarkerFill.color.val = MarkerFill; xy.MarkerLine.width.val = '0.5pt'    

    fig_NCl = vplot([V30**vs_], [NNcl[0][idx30]], xname = 'V30_'+dname, yname = 'N30_cl_'+dname,color=color, marker= 'square', markersize = '6pt', g = fig_NCl)
    xy.MarkerLine.color.val = MarkerLine; xy.MarkerFill.color.val = MarkerFill; xy.MarkerLine.width.val = '0.5pt'
    
    fig_NCl = vplot( VV**vs_,    NNcl,            xname = 'V_'+dname,   yname = 'N_cl_'+dname,  color=color, style = 'solid', markersize = MarkerSize, g = fig_NCl, keylabel=label)
    xy.MarkerLine.color.val = MarkerLine; xy.MarkerFill.color.val = MarkerFill; xy.MarkerLine.width.val = '0.5pt'
    xy.PlotLine.bezierJoin.val = True; xy.PlotLine.width.val = PlotLineWidth; xy.PlotLine.style.val = PlotLineStyle
    
    fig_NCl.Root.notes.val = 'gel_Cl'+'_log' * x.log.val +'_'+xlabel

    graph_NCl = fig_NCl.Root.page1.graph1
    for i in ['max', 'min', 'log', 'label']:
        exec('graph_NCl.x.'+i+'.val = x.'+i+'.val')
    graph_NCl.y.label.val = '\\Delta N_{Cl}/N_{gel}'

    if rand_g.p['Ca']**-1:
        fig_NCa = vplot([V00**vs_], [NNca[0][idx00]], xname = 'Veq_'+dname, yname = 'N00_ca_'+dname,color=color, marker= 'circle', markersize = '6pt', g = fig_NCa)
        xy.MarkerLine.color.val = MarkerLine; xy.MarkerFill.color.val = MarkerFill; xy.MarkerLine.width.val = '0.5pt'
    
        fig_NCa = vplot([V10**vs_], [NNca[0][idx10]], xname = 'V10_'+dname, yname = 'N10_ca_'+dname,color=color, marker= 'cross', markersize = '6pt', g = fig_NCa)
        xy.MarkerLine.color.val = MarkerLine; xy.MarkerFill.color.val = MarkerFill; xy.MarkerLine.width.val = '0.5pt'    
    
        fig_NCa = vplot([V30**vs_], [NNca[0][idx30]], xname = 'V30_'+dname, yname = 'N30_ca_'+dname,color=color, marker= 'square', markersize = '6pt', g = fig_NCa)
        xy.MarkerLine.color.val = MarkerLine; xy.MarkerFill.color.val = MarkerFill; xy.MarkerLine.width.val = '0.5pt'
        fig_NCa = vplot( VV**vs_,    NNca,            xname = 'V_'+dname,   yname = 'N_ca_'+dname,  color=color, style = 'solid', markersize = MarkerSize, g = fig_NCa, keylabel=label)
        xy.MarkerLine.color.val = MarkerLine; xy.MarkerFill.color.val = MarkerFill; xy.MarkerLine.width.val = '0.5pt'
        xy.PlotLine.bezierJoin.val = True; xy.PlotLine.width.val = PlotLineWidth; xy.PlotLine.style.val = PlotLineStyle
        
        fig_NCa.Root.notes.val = 'gel_Ca'+'_log' * x.log.val +'_'+xlabel

        graph_NCa = fig_NCa.Root.page1.graph1
        for i in ['max', 'min', 'log', 'label']:
            exec('graph_NCa.x.'+i+'.val = x.'+i+'.val')
        graph_NCa.y.label.val = '\\Delta N_{Ca}/N_{gel}'


    return [fig_PV, fig_alpha, fig_NNa, fig_NCl, fig_NCa ]


def add_acfs(GG, color='black', figs = figs, idx = None ):
    [fig_PV, fig_alpha, fig_NNa, fig_NCl, fig_NCa] = figs

    ################## Plot the acf for random gel ########################
    #if idx is set then plot acf of GG[idx] 
    if idx==None: rand_g = np.random.choice(GG)
    #rand_g = GG[-5]

    Na_acf  = autocorrelation( rand_g.Samples['Na'][:,0]      )[0]
    Cl_acf  = autocorrelation( rand_g.Samples['Cl'][:,0]      )[0]

    P_acf   = autocorrelation( rand_g.Samples['pressure'][:,0])[0]
    Re_acf  = autocorrelation( rand_g.Samples['Re00'][:,0]    )[0]
    PA_acf  = autocorrelation( rand_g.Samples['PA'][:,0]      )[0]

    fig_NNa.SetData('Na_acfy_'+str(rand_g), Na_acf)
    fig_NNa.SetData('Na_acfx_'+str(rand_g), range(len(Na_acf)))

    fig_NCl.SetData('Cl_acfy_'+str(rand_g), Cl_acf)
    fig_NCl.SetData('Cl_acfx_'+str(rand_g), range(len(Cl_acf)))

    if rand_g.p['Ca']**-1:
        Ca_acf  = autocorrelation( rand_g.Samples['Ca'][:,0]      )[0]
        fig_NCa.SetData('Ca_acfy_'+str(rand_g), Ca_acf)
        fig_NCa.SetData('Ca_acfx_'+str(rand_g), range(len(Ca_acf)))
    else:
        figs=figs[:-1]

    fig_PV.SetData('Re_acfy_'+str(rand_g), Re_acf)
    fig_PV.SetData('Re_acfx_'+str(rand_g), range(len(Re_acf)))

    fig_PV.SetData('P_acfy_'+str(rand_g), P_acf)
    fig_PV.SetData('P_acfx_'+str(rand_g), range(len(P_acf)))

    fig_alpha.SetData('PA_acfy_'+str(rand_g), P_acf)
    fig_alpha.SetData('PA_acfx_'+str(rand_g), range(len(P_acf)))


    for fig in figs:
        page = fig.Root.Add('page')
        graph = page.Add('graph')
        graph.Add('key')
        acfy = [s for s in fig.GetDatasets() if 'acfy_'+str(rand_g) in s]
        for acf in acfy:
            acfx = acf.replace('acfy_', 'acfx_')
            keylabel = acf.split('_')[0]
            addxy(  graph,
                x_dataname=acfx, y_dataname=acf, marker='cross', markersize='2pt', color = color, keylabel = keylabel, xname='Samples', yname='ACF')
        label = graph.Add('label')
        label.label.val = str(rand_g).replace('_','\_')



    ################## Plot the acf for random gel ########################
    return [fig_PV, fig_alpha, fig_NNa, fig_NCl, fig_NCa]



def plotAlphaP(GG, label, title, color='black', fig = fig_alphaP):
    print('##################################')
    fig_alphaP = fig

    [idx00, idx10, idx30] = getR_eq(GG)

    P00 = PP[0][idx00]
    P10 = PP[0][idx10]
    P30 = PP[0][idx30]
    V00 = VV[idx00]
    V10 = VV[idx10]
    V30 = VV[idx30]
    NA00 = NNA[0][idx00]
    NA10 = NNA[0][idx10]
    NA30 = NNA[0][idx30]

    dname = GG[0].name.replace('box_l'+str(GG[0].box_l)+'_','').replace('_N'+str(GG[0].N_Samples), '')

    fig_alphaP = vplot([P00], [NA00/rand_g.MPC/16], xname = 'V00_'+dname, yname = 'alpha00_'+dname,color=color, marker= 'circle', markersize = '4pt', g = fig_alphaP)
    fig_alphaP = vplot([P10], [NA10/rand_g.MPC/16], xname = 'V10_'+dname, yname = 'alpha10_'+dname,color=color, marker= 'cross', markersize = '4pt', g = fig_alphaP)
    fig_alphaP = vplot([P30], [NA30/rand_g.MPC/16], xname = 'V30_'+dname, yname = 'alpha30_'+dname,color=color, marker= 'square', markersize = '4pt', g = fig_alphaP)
    fig_alphaP = vplot( PP,    NNA/rand_g.MPC/16,   xname = 'V_'+dname,   yname = 'alpha_'+dname,  color=color, style = 'solid', g = fig_alphaP, keylabel=label)
    fig_alphaP = vplot( PP,    alphaDonnan_arr,     xname = 'V_'+dname,   yname = 'alphaDonnan_'+dname,color=color, marker='none', style = 'dotted', g = fig_alphaP)
    graph_alphaP = fig_alphaP.Root.page1.graph1

    x = graph_alphaP.x
    y = graph_alphaP.y
    y.min.val = 0
    y.max.val = 1.05
    y.label.val = '\\alpha'

    x.max.val = 31
    x.min.val = -2.5
    x.log.val = False

    xlabel = 'pressure'
    x.label.val = '\Delta P = P - P^{res}, bar'

    fig_alphaP.Root.notes.val = 'gel_alpha'+'_log' * x.log.val +'_'+xlabel


    return fig_alphaP









def plotN(GG, label, ion, title, color='black', fig = fig_N):


    [Req, Peq, R10, P10] = getR_eq(GG)
    Ngel_arr = []
    Nout_arr = []
    RR = []
    rand_g = np.random.choice(GG)
    try: Nacid = rand_g.MPC*16
    except AttributeError: Nacid = rand_g.Nacid

    for g in GG:

        RR.append(g.box_l)
        Ngel_arr.append([g.Means[ion], g.Erros[ion]])


    # ~ Vbox = np.max(RR)**3
    # ~ if not sigma:
        # ~ R_eq = max(RR)
    bulk = rand_g.getbulk()
    N = (rand_g.MPC*16+8)

    Vbox = Req**3
    idx_eq = (RR== Req).argmax()
    idx_10 = (RR== R10).argmax()

    Nout_arr = (Vbox - np.array(RR)**3) * bulk.Means[ion] / bulk.box_l**3
    Nout_err = (Vbox - np.array(RR)**3) * bulk.Erros[ion] / bulk.box_l**3
    Nout_arr = np.array([Nout_arr, Nout_err])

    Ngel_arr = np.array(Ngel_arr).T
    Ntot_arr = Ngel_arr[0]+Nout_arr[0]
    Ntot_err = Ngel_arr[1]+Nout_arr[1]
    Ntot_arr = np.array([Ntot_arr, Ntot_err])

    Ntot_arr[0]  -= Ntot_arr[0][idx_eq]
    Ntot_arr[0] /= N
    Ntot_arr[1] /= N

    dname = GG[0].name.replace('box_l'+str(GG[0].box_l)+'_','').replace('_N'+str(GG[0].N_Samples), '')


    # These three lines plot the circle indicating the place where Pressure is zero
    #idx_eq = (RR == R_eq).argmax()
    print ('##########################', Req, Ntot_arr[0][idx_eq], Ntot_arr[0])
    fig = vplot([1/Veq], [Ntot_arr[0][idx_eq]], xname = 'Veq_'+dname, yname = 'Neq_'+ion+'_'+dname,color=color, marker= 'circle', markersize = '4pt', g = fig)
    fig = vplot([1/V10], [Ntot_arr[0][idx_10]], xname = 'V10_'+dname, yname = 'N10_'+ion+'_'+dname,color=color, marker= 'circle', markersize = '4pt', g = fig)
    xy.MarkerLine.color.val = color
    xy.MarkerLine.width.val = '1pt'
    xy.MarkerFill.color.val = 'white'


    fig = vplot(1/VV, Ntot_arr, xname = 'R_'+dname, yname = 'N_'+ion+'_'+dname, color=color, style = 'dotted', g = fig, keylabel=label)
    fig.Root.notes.val = 'gel_'+ion

    page = fig.Root.page1
    graph = page.graph1
    # ~ xy.PlotLine.width.val = '4pt'
    # ~ graph.x.min.val = 1
    # ~ graph.y.min.val = 0
    # ~ graph.y.max.val = 1.01
    graph.x.max.val = 8
    graph.x.min.val = 0.1
    graph.x.log.val = False
    fig.Root.notes.val += '_log'*graph.x.log.val
    page.width.val = str(figsize)+'cm'
    page.height.val = str(figsize / aspect)+'cm'

    # ~ pagePV.width.val = width
    # ~ pagePV.height.val = height


    # ~ graph.x.label.val = 'box length, \sigma'
    graph.x.label.val = 'V, l/mol'
    graph.y.label.val = 'N^{box}_'+ion+'}'

    ################## Plot the acf for random gel ########################
    # ~ rand_g = np.random.choice(GG)
    N4acf = rand_g.Samples[ion][:,0]
    ACF_N = autocorrelation(N4acf)[0]

    fig.SetData('ACF_'+ion+'_y'+str(rand_g), ACF_N)
    fig.SetData('ACF_'+ion+'_x'+str(rand_g), range(len(ACF_N)))

    page_acf = fig.Root.Add('page')
    graph_acf = page_acf.Add('graph')
    graph_acf.Add('key')
    addxy(graph_acf,
            x_dataname='ACF_'+ion+'_x'+str(rand_g),
            y_dataname='ACF_'+ion+'_y'+str(rand_g),
            marker='cross', markersize='2pt', color = color, keylabel = 'PA', xname='Samples', yname='ACF')
    label = graph_acf.Add('label')
    label.label.val = str(rand_g).replace('_','\_')

    ################## Plot the acf for random gel ########################
    return fig



def plotAlpha(GG, label, title, color='black', fig = fig_alpha):
    [Req, Peq, R10, P10] = getR_eq(GG)

    PA_arr = []
    alphaDonnan_arr = []
    RR = []
    rand_g = np.random.choice(GG)
    bulk = rand_g.getbulk()
    try: Nacid = rand_g.MPC*16
    except AttributeError: Nacid = rand_g.Nacid

    for g in GG:
        RR.append(g.box_l)
        if abs(g.p['K']) != np.inf:
            PA_arr.append([g.Means['PA'], g.Erros['PA']])
            cs = bulk.Means['Na'] / bulk.box_l**3 # !important. For multivalent ions here must be an ionic strength
            cp = g.MPC*16 / g.box_l**3 #The number of ionogenic groups (the nodes are excluded)
            alphaDonnan_arr.append(alphaDonnan(cp, cs, g.p['H'], g.p['K']))
        else:
            PADonnan_arr.append(1)
            PA_arr.append([g.MPC*16, 0])

    PA_arr = np.array(PA_arr).T
    AAlpha = PA_arr / Nacid

    # label = r'$c^{bulk}_s$ = '+'{:.3f} mol/l'.format(rand_g.cs_bulk)+r', $\mathrm{p}K = $'+str(pK)
    # ~ if abs(g.p['K']) != np.infty:
        # ~ if not 'fig_alpha' in globals():
            # ~ fig_alpha = plt.figure(figsize=(figsize * aspect,figsize))
            # ~ ax_alpha = fig_alpha.add_axes([0.12,0.12,0.85,0.75])
            # ~ plt.title(title)


        # ~ ax_alpha.errorbar(RR, AAlpha[0], AAlpha[1], linestyle=':',marker='o', label=label, color=color)


    # These three lines plot the circle indicating the place where Pressure is zero
    idx_eq = (RR == Req).argmax()
    idx_10 = (RR == R10).argmax()
    dname = GG[0].name.replace('box_l'+str(GG[0].box_l)+'_','').replace('_N'+str(GG[0].N_Samples), '')
    fig = vplot([1/Veq], [AAlpha[0][idx_eq]], xname = 'Req_'+dname, yname = 'alphaeq_'+dname,color=color, marker= 'circle', markersize = '4pt', g = fig)
    fig = vplot([1/V10], [AAlpha[0][idx_10]], xname = 'R10_'+dname, yname = 'alpha10_'+dname,color=color, marker= 'circle', markersize = '4pt', g = fig)
    xy.MarkerLine.color.val = color
    xy.MarkerLine.width.val = '1pt'
    xy.MarkerFill.color.val = 'white'


    fig = vplot(1/VV, AAlpha, xname = 'R_'+dname, yname = 'alpha_'+dname,color=color, style = 'dotted', g = fig, keylabel=label)
    fig = vplot(1/VV, alphaDonnan_arr, xname = 'R_'+dname, yname = 'alphaDonnan_'+dname,color=color, marker='none', style = 'solid', g = fig)

    fig.Root.notes.val = 'gel_alpha'
    page = fig.Root.page1
    graph = page.graph1
    # ~ xy.PlotLine.width.val = '4pt'
    # ~ graph.x.min.val = 1

    graph.y.min.val = 0
    graph.y.max.val = 1.01
    graph.x.max.val = 3
    graph.x.min.val = 'auto'
    graph.x.log.val = False
    fig.Root.notes.val += '_log'*graph.x.log.val
    page.width.val = str(figsize)+'cm'
    page.height.val = str(figsize / aspect)+'cm'

    # ~ pagePV.width.val = width
    # ~ pagePV.height.val = height


    # ~ graph.x.label.val = 'box length, \sigma'
    graph.x.label.val = 'V, l/mol'
    graph.y.label.val = '\\alpha'

    ################## Plot the acf for random gel ########################
    # ~ rand_g = np.random.choice(GG)
    PA4acf = rand_g.Samples['PA'][:,0]
    ACF_PA = autocorrelation(PA4acf)[0]
    fig.SetData('ACF_alpha_y'+str(rand_g), ACF_PA)
    fig.SetData('ACF_alpha_x'+str(rand_g), range(len(ACF_PA)))

    page_acf = fig.Root.Add('page')
    graph_acf = page_acf.Add('graph')
    graph_acf.Add('key')
    addxy(graph_acf,
            x_dataname='ACF_alpha_x'+str(rand_g),
            y_dataname='ACF_alpha_y'+str(rand_g),
            marker='cross', markersize='2pt', color = color, keylabel = 'PA', xname='Samples', yname='ACF')
    label = graph_acf.Add('label')
    label.label.val = str(rand_g).replace('_','\_')


    ################## Plot the acf for random gel ########################

    return fig












