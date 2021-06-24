#%%
import random
import math
import numpy as np
import csv

#import sys
#import logging
#logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

from socket_server import Server

server = Server('127.0.0.1', 10004)
server.setup()
server.start()

import subprocess
try:
    clientA = subprocess.Popen(['/home/ml/espresso/build/pypresso', 'esp_client.py', '10'])
    clientB = subprocess.Popen(['/home/ml/espresso/build/pypresso', 'esp_client.py', '5'])
except:
    server.server_socket.close()

#wait for clients to connect
while len(server.addr_list)<3:
    pass

#server.request("system.change_volume_and_rescale_particles(10*2**(1/3), dir='xyz')", 0)
#server.request("system.change_volume_and_rescale_particles(10, dir='xyz')", 1)

for i in range(500):
    server.request("system.part.add(pos=system.box_l * np.random.random(3))", 1, wait = False)
server.request("len(system.part[:])", 0)

for i in range(500):
    server.request("system.part.add(pos=system.box_l * np.random.random(3))", 1, wait = False)
server.request("len(system.part[:])", 1)

server.request("system.thermostat.set_langevin(kT=1, gamma=1, seed=42)",0, wait = False)
server.request("system.thermostat.set_langevin(kT=1, gamma=1, seed=42)",1, wait = False)
server.request(["system.minimize_energy.init(f_max=50, gamma=30.0, max_steps=10000, max_displacement=0.001)",
                "system.minimize_energy.minimize()"],0, wait = False)    
server.request(["system.minimize_energy.init(f_max=50, gamma=30.0, max_steps=10000, max_displacement=0.001)",
                "system.minimize_energy.minimize()"],1, wait = False)        

server.request("float(system.analysis.energy()['total'])",0)
server.request("float(system.analysis.energy()['total'])",1)   
#%%
def md(n, steps : int):
    print(server.request(f"system.integrator.run({steps})", n))

#md(1,100)
#%%
from scipy.spatial.transform import Rotation
def entropy_change(N1, N2, V1, V2):
    #N1, V1 - box we removing particle from
    #N2, V2 - box we adding to
    return math.log((N1*V2)/((N2+1)*V1))

def monte_carlo_accept(delta_fenergy, beta):
    if delta_fenergy<0:
        return True
    else:
        prob = math.exp(-delta_fenergy)
        return (prob > random.random())


class monte_carlo:
    def __init__(self, server, beta) -> None:
        self.server = server
        self.beta = beta
        self.server.request(["float(system.analysis.energy()['total'])",
                    "list(system.part[:].id)",
                    "system.box_l"],0, wait = False)
        self.server.request(["float(system.analysis.energy()['total'])",
                        "list(system.part[:].id)",
                        "system.box_l"],1, wait = False)
        self.server.wait_all()
        self.energy = [None]*2
        self.IDs = [None]*2
        self.box = [None]*2
        self.energy[0], self.IDs[0], self.box[0] = self.server.responce(0)
        self.energy[1], self.IDs[1], self.box[1] = self.server.responce(1)
        
        self.n_part = [len(self.IDs[0]), len(self.IDs[1])]
        self.vol = [float(np.prod(self.box[0])), float(np.prod(self.box[1]))]

        #print(self.energy)

        f = open('result.csv', 'w')
        writer = csv.writer(f)
        writer.writerow(['step','ΔE','ΔS', 'left','right', 'E'])
        f.close()

    def __call__(self, repeats = 1) -> None:
        f = open('result.csv', 'a')
        writer = csv.writer(f)
        for i in range(repeats):
            #side = int(random.random() > self.n_part[0]/sum(self.n_part))
            
            side = random.choice([0,1])
            if self.n_part[side] == 0:
                side = int(not(side))

            rnd_id = random.choice(self.IDs[side])
            
            other_side = int(not(side))

            print(f"{side} -> {other_side}, {rnd_id}")
            
            #remember removed particle position and velocity
            #then remove it and get new energy
            removed_part_pos, removed_part_v, _, = server.request([
                f"list(system.part[{rnd_id}].pos)",
                f"list(system.part[{rnd_id}].v)",
                f"system.part[{rnd_id}].remove()",
                ],
                side)
            server.request(
                "float(system.analysis.energy()['total'] - system.analysis.energy()['kinetic'])",
                side, wait=False) #takes longer so we collect the result later (*)

            #before the move, randomly rotate velocity    
            rot = Rotation.random().as_matrix()
            add_part_v = list(rot.dot(removed_part_v))

            #add new particle to the other side, remember id, get new energy
            self.server.request([
                f"int(system.part.add(pos=system.box_l * np.random.random(3), v = {add_part_v}).id)",
                "float(system.analysis.energy()['total']-system.analysis.energy()['kinetic'])",
                ],
                other_side, wait=False) #this will be collected later too (+)

            #collect responces from clients
            self.server.wait_all()
            energy_after_removal = self.server.responce(side) #here we collect energy (*)
            add_part_id, energy_after_add = self.server.responce(other_side) #collect add_part_id and energy (+)
            #get thermodynamic potentials change
            delta_E = energy_after_removal+energy_after_add - sum(self.energy)
            delta_S = entropy_change(self.n_part[side], self.n_part[other_side], self.vol[side], self.vol[other_side])
            delta_F = delta_E - delta_S
            #delta_F = -delta_S/self.beta


            if monte_carlo_accept(delta_F, self.beta):
                print('Move accepted')
                #store new state
                self.energy[side] = energy_after_removal
                self.energy[other_side] = energy_after_add
                self.IDs[side].remove(rnd_id)
                self.IDs[other_side].append(add_part_id)
                self.n_part = [len(self.IDs[0]), len(self.IDs[1])]
                print(f"step:{i}, ΔE: {delta_E}, ΔS: {delta_S}, particles: {self.n_part}") 
            else:
                print('Move rejected')
                #undo removal and set speed
                self.server.request(
                    f"system.part.add(pos={removed_part_pos}, id = {rnd_id}, v = {removed_part_v}).id", 
                    side, wait=False)
                
                #remove last added particle
                self.server.request(f"system.part[{add_part_id}].remove()", other_side, wait = False)
            writer.writerow([i, delta_E, delta_S, self.n_part[0],self.n_part[1], sum(self.energy)])
        f.close()
# %%
mc = monte_carlo(server, 1)
#%%
for i in range(10):
    print(f'round {i}')
    mc(100)
    md(0,1000)
    md(1,1000)
# %%
import pandas as pd
df = pd.read_csv('result.csv')
df = df.reset_index()
#%%
import matplotlib.pyplot as plt
import seaborn as sns

df.left = df.left/mc.vol[0]
df.right = df.right/mc.vol[1]

sns.lineplot(data=df, x='index', y = 'left')
sns.lineplot(data=df, x='index', y = 'right')
plt.show()

sns.lineplot(data = df, x='index', y = 'ΔS')
plt.show()

sns.lineplot(data = df[200:], x='index', y = 'E')
plt.show()
# %%
box = server.request("system.box_l", 0)
vol0 = float(np.prod(box))
box = server.request("system.box_l", 1)
vol1 = float(np.prod(box))
# %%
vol1/vol0
# %%
pos = mc.server.request("system.part[:].pos", 1).T

# %%
import plotly.express as px

px.scatter_3d(x = pos[0], y = pos[1], z = pos[2])
# %%
mc(300)
# %%
md(0,10000)
md(1,10000)
# %%
mc.beta=1
# %%
