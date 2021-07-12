#%%
import random
import math
import numpy as np
import csv
from tqdm import tqdm

#import sys
#import logging
#logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

from socket_server import Server
#%%
ELECTROSTATIC =False
V_all = 40**3*2
v = 0.3
V = [V_all*(1-v),V_all*v]
l = [V_**(1/3) for V_ in V]
l_bjerrum = 2.0
temp = 1
N1 = 80
N2 = 60
N_anion_fixed = 10
#%%
server = Server('127.0.0.1', 10002)
server.setup()
server.start()

import os
import sys
os.chdir(sys.path[0])
import subprocess
try:
    clientA = subprocess.Popen(['/home/ml/espresso/build/pypresso', 'esp_client_charged.py', str(l[0])])
    while len(server.addr_list)<2:
        pass
    clientB = subprocess.Popen(['/home/ml/espresso/build/pypresso', 'esp_client_charged.py', str(l[1])])
    while len(server.addr_list)<3:
        pass
except:
    server.server_socket.close()
    sys.exit()
#%%
##populate the systems##
for i in range(int(N1/2)):
    server.request(
        [
        "system.part.add(pos=system.box_l * np.random.random(3), type = 0, q = -1.0)",
        "system.part.add(pos=system.box_l * np.random.random(3), type = 1, q = +1.0)"
        ], 0, wait = False)

for i in range(int(N2/2)):
    server.request(
        [
        "system.part.add(pos=system.box_l * np.random.random(3), type = 0, q = -1.0)",
        "system.part.add(pos=system.box_l * np.random.random(3), type = 1, q = +1.0)",
        ], 1, wait = False)

for i in range(N_anion_fixed):
    server.request(
        [
        "system.part.add(pos=system.box_l * np.random.random(3), type = 2, q = -1.0)",
        "system.part.add(pos=system.box_l * np.random.random(3), type = 1, q = +1.0)"
        ],
        1, wait = False)

##add LJ interactions### 
server.request(
        [
        "system.non_bonded_inter[0, 0].lennard_jones.set_params(epsilon=1, sigma=1, cutoff=3, shift='auto')",
        "system.non_bonded_inter[0, 1].lennard_jones.set_params(epsilon=1, sigma=1, cutoff=3, shift='auto')",
        "system.non_bonded_inter[1, 1].lennard_jones.set_params(epsilon=1, sigma=1, cutoff=3, shift='auto')",
        "system.non_bonded_inter[0, 2].lennard_jones.set_params(epsilon=1, sigma=1, cutoff=3, shift='auto')",
        "system.non_bonded_inter[1, 2].lennard_jones.set_params(epsilon=1, sigma=1, cutoff=3, shift='auto')",
        "system.non_bonded_inter[2, 2].lennard_jones.set_params(epsilon=1, sigma=1, cutoff=3, shift='auto')"
        ], 
        [0,1], 
        wait = False
    )
server.request(["system.thermostat.set_langevin(kT=1, gamma=1, seed=42)",
                "system.minimize_energy.init(f_max=50, gamma=30.0, max_steps=10000, max_displacement=0.001)",
                "system.minimize_energy.minimize()"
                ],
                [0,1], 
                wait = False)       


##switch on electrostatics
if ELECTROSTATIC:
    server.request(f"system.actors.add(electrostatics.P3M(prefactor={l_bjerrum * temp},accuracy=1e-3))",[0,1])


#minimize energy and run md
server.request(["system.minimize_energy.init(f_max=50, gamma=30.0, max_steps=10000, max_displacement=0.001)",
                "system.minimize_energy.minimize()"],0, wait = False)    
server.request(["system.minimize_energy.init(f_max=50, gamma=30.0, max_steps=10000, max_displacement=0.001)",
                "system.minimize_energy.minimize()"],1, wait = False)
server.request(f"system.integrator.run({10000})", [0,1])
# %%
## plot the particles in box
def scatter_box(server, n):
    import plotly.express as px
    pos = server.request("system.part[:].pos", n).T
    types = server.request("system.part[:].type", n).T
    color_dict={
        0:'anion',
        1:'cation',
        2:'anion_fixed'
    }
    px.scatter_3d(x = pos[0], y = pos[1], z = pos[2], color=[color_dict[type_] for type_ in types])
scatter_box(server, 1)
# %%
from scipy.spatial.transform import Rotation
def entropy_change(N1, N2, V1, V2, n=1):
    #N1, V1 - box we removing particle from
    #N2, V2 - box we adding to
    #n - number of particles 
    if n==1:
        return math.log((N1*V2)/((N2+1)*V1))
    elif n==2:
        return math.log((V2/V1)**2*(N1*(N1-1))/((N2+2)*(N2+1)))

def monte_carlo_accept(delta_fenergy, beta):
    if delta_fenergy<0:
        return True
    else:
        prob = math.exp(-beta*delta_fenergy)
        return (prob > random.random())

class monte_carlo_charged_pairs:
    def __init__(self, server, beta, log_fname) -> None:
        self.server = server
        self.beta = beta
        self.log_fname = log_fname
        self.server.request(["float(system.analysis.energy()['total'])",
                    "[list(system.part.select(type=0).id), list(system.part.select(type=1).id)]",
                    "system.box_l"],[0,1], wait = False)
        self.energy = [None]*2
        self.IDs = [None]*2
        self.box = [None]*2
        self.server.wait_all()
        for i in range(2):
            self.energy[i], self.IDs[i], self.box[i] = self.server.responce(i)
        
        self.n_part = [ len(self.IDs[0][0])+len(self.IDs[0][1]),
                        len(self.IDs[1][0])+len(self.IDs[1][1])]
        
        self.vol = [float(np.prod(self.box[0])), float(np.prod(self.box[1]))]
        
        f = open(self.log_fname, 'w')
        writer = csv.writer(f)
        writer.writerow(['step','ΔE','ΔS', 'left-', 'left+', 'right-', 'right+', 'E'])
        f.close()

    def __call__(self, repeats = 1) -> None:
        f = open(self.log_fname, 'a')
        accepted = 0
        writer = csv.writer(f)
        for i in tqdm(range(repeats)):

            side = random.choice([0,1])
            if self.n_part[side] == 0:
                side = int(not(side))

            rnd_id_anion = random.choice(self.IDs[side][0])
            rnd_id_cation = random.choice(self.IDs[side][1])
            
            other_side = int(not(side))
            
            #remember removed pair position and velocity
            #then remove it and get new energy
            removed_anion_pos, removed_cation_pos, removed_anion_v, removed_cation_v, *_ = server.request(
                [
                f"list(system.part[{rnd_id_anion}].pos)", 
                f"list(system.part[{rnd_id_cation}].pos)",
                f"list(system.part[{rnd_id_anion}].v)",
                f"list(system.part[{rnd_id_cation}].v)",
                f"system.part[{rnd_id_anion}].remove()",
                f"system.part[{rnd_id_cation}].remove()",
                ],
                side)
            server.request(
                "float(system.analysis.energy()['total'] - system.analysis.energy()['kinetic'])",
                side, wait=False) #takes longer so we collect the result later (*)

            #before the move, randomly rotate velocity    
            rot0 = Rotation.random().as_matrix()
            rot1 = Rotation.random().as_matrix()
            add_anion_v, add_cation_v = [list(rot0.dot(removed_anion_v)),list(rot1.dot(removed_cation_v))] 

            #add new particle to the other side, remember id, get new energy
            self.server.request([
                f"int(system.part.add(pos=system.box_l * np.random.random(3), v = {add_anion_v}, q = -1.0, type = 0).id)",
                f"int(system.part.add(pos=system.box_l * np.random.random(3), v = {add_cation_v}, q = +1.0, type = 1).id)",
                "float(system.analysis.energy()['total']-system.analysis.energy()['kinetic'])",
                ],
                other_side, wait=False) #this will be collected later too (+)

            #collect responces from clients
            self.server.wait_all()
            energy_after_removal = self.server.responce(side) #here we collect energy (*)
            add_anion_id, add_cation_id, energy_after_add = self.server.responce(other_side) #collect add_part_id and energy (+)
            
            
            #get thermodynamic potentials change
            delta_E = energy_after_removal+energy_after_add - sum(self.energy)
            delta_S = entropy_change(self.n_part[side], self.n_part[other_side], self.vol[side], self.vol[other_side], n=2)
            delta_F = delta_E - delta_S
            #delta_F = -delta_S


            if monte_carlo_accept(delta_F, self.beta):
                accepted +=1
                tqdm.write(f"{side} -> {other_side} accepted")
                #store new state
                self.energy[side] = energy_after_removal
                self.energy[other_side] = energy_after_add
                
                self.IDs[side][0].remove(rnd_id_anion)
                self.IDs[side][1].remove(rnd_id_cation)
                self.IDs[other_side][0].append(add_anion_id)
                self.IDs[other_side][1].append(add_cation_id)
                
                self.n_part = [ len(self.IDs[0][0])+len(self.IDs[0][1]),
                                len(self.IDs[1][0])+len(self.IDs[1][1])]
                #print(f"step:{i}, ΔE: {delta_E}, ΔS: {delta_S}, particles: {self.n_part}") 
            else:
                tqdm.write(f"{side} -> {other_side} rejected")
                #undo removal and set speed
                self.server.request(
                    [
                    f"system.part.add(pos={removed_anion_pos}, id = {rnd_id_anion}, v = {removed_anion_v}, q = -1.0, type = 0).id",
                    f"system.part.add(pos={removed_cation_pos}, id = {rnd_id_cation}, v = {removed_cation_v}, q = +1.0, type = 1).id",
                    ], 
                    side, wait=False)
                
                #remove last added particle
                self.server.request(
                    [
                    f"system.part[{add_anion_id}].remove()",
                    f"system.part[{add_cation_id}].remove()",
                    ], other_side, wait = False)
            writer.writerow([i, delta_E, delta_S, len(self.IDs[0][0]), len(self.IDs[0][1]), len(self.IDs[1][0]), len(self.IDs[1][1]), sum(self.energy)])
        f.close()
        return accepted
# %%
mc = monte_carlo_charged_pairs(server, beta=1, log_fname=f'result_{v}.csv')
# %%
##warmup
rounds = 20
mc_moves = 500
at_least_accepted = 100
md_steps = 100000
for i in tqdm(range(rounds)):
    accepted = mc(mc_moves)
    while accepted<at_least_accepted:
        tqdm.write('Not enough MC moves')
        mc.server.request(f"system.integrator.run({100000})", [0,1])
        accepted += mc(300) 
    mc.server.request(f"system.integrator.run({100000})", [0,1])
##collect_data
n_points = 3
sample_size = 1000
for i in tqdm(range(n_points)):
    mc(sample_size)
    mc.server.request(f"system.integrator.run({100000})", [0,1])
mc(sample_size)

#%%
#v=0.3
import pandas as pd
#df = pd.read_csv(mc.log_fname)
df = pd.read_csv(f'result_{0.3}.csv')
df = df.reset_index()
#%%
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

plot_df = df.melt('index', value_vars=['left-', 'left+', 'right-', 'right+'])
sns.lineplot(data=plot_df, x='index', y = 'value', hue = 'variable')
plt.show()

smooth = lambda _: np.convolve(_, np.ones(100)/100, mode='valid')
plt.plot(smooth(df['left-']+df['left+']), label = 'left')
plt.plot(smooth(df['right-']+df['right+']), label = 'right')
plt.legend()
plt.show()

sns.lineplot(data = df, x='index', y = 'ΔS')
plt.show()

plt.plot(smooth(df['E']))
plt.show()
# %%
n_points = 3
sample_size = 500

import os
if not os.path.isfile('dzeta.csv'):
    with open('dzeta.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['lm','lp','rm','rp','lv','rv', 'std', 'electrostatic'])
with open('dzeta.csv', 'a') as f:
    writer = csv.writer(f)
    result = df[:-sample_size*i]
    for i in range(1,n_points+1):

        result = df[sample_size*(i-1):sample_size*i].mean()
        std = df['left-'][:sample_size*i].std().squeeze()
        writer.writerow([result['left-'], result['left+'],
                        result['right-'],result['right+'],
                        V[0],V[1], std, ELECTROSTATIC])

server.active = False
#%%
import pandas as pd
df = pd.read_csv(f'dzeta.csv')
df = df.reset_index()
#%%
import seaborn as sns
df['dzeta'] = df.lm/df.lv/(df.rm/df.rv)
df['v'] = df.rv/(df.rv+df.lv)
df['cs'] = (df.lm+df.lp)/2/df.lv
sns.scatterplot(data = df, x = 'v', y = 'dzeta', hue = 'electrostatic')

# %%
