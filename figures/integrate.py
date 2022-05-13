from veusz_embed import *
pp = gibbs_df.P[11][0]
phi = gibbs_df.phi[11]         
vv = 1/phi
(fig, graph, xy) = vplot (phi,pp)  
from scipy import optimize        
def function(v, a, gamma):
   return a*v**(-gamma)
   
   
   
popt,cov = scipy.optimize.curve_fit(function, vv, pp)

fun= graph.Add('function') 
a,gamma = popt
#fun.function.val =f'{a}*x+{b}'
fun.function.val =f'{a}*x**{gamma}'


from scipy import integrate       
integrate.simps(pp,vv)
