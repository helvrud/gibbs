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
    clientA = subprocess.Popen(['/home/ml/espresso/build/pypresso', 'esp_client_charged.py', '20'])
    clientB = subprocess.Popen(['/home/ml/espresso/build/pypresso', 'esp_client_charged.py', '40'])
except:
    server.server_socket.close()

#wait for clients to connect
while len(server.addr_list)<3:
    pass

l_bjerrum = 7.0
temp = 1
N1 = 80
N2 = 10

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
        "system.part.add(pos=system.box_l * np.random.random(3), type = 1, q = +1.0)"
        ], 1, wait = False)

server.request(["system.thermostat.set_langevin(kT=1, gamma=1, seed=42)",
                "system.minimize_energy.init(f_max=50, gamma=30.0, max_steps=10000, max_displacement=0.001)",
                "system.minimize_energy.minimize()"
                ],
                [0,1], 
                wait = False)       



server.request(
        [
        "system.non_bonded_inter[0, 0].lennard_jones.set_params(epsilon=1, sigma=1, cutoff=3, shift='auto')",
        "system.non_bonded_inter[0, 1].lennard_jones.set_params(epsilon=1, sigma=1, cutoff=3, shift='auto')",
        "system.non_bonded_inter[1, 1].lennard_jones.set_params(epsilon=1, sigma=1, cutoff=3, shift='auto')"
        ], 
        [0,1], 
        wait = False
    )

server.request(f"system.actors.add(electrostatics.P3M(prefactor={l_bjerrum * temp},accuracy=1e-3))",[0,1])

print(server.request("system.analysis.energy()",[0,1]))
# %%
server.request(["system.minimize_energy.init(f_max=50, gamma=30.0, max_steps=10000, max_displacement=0.001)",
                "system.minimize_energy.minimize()"],0, wait = False)    
server.request(["system.minimize_energy.init(f_max=50, gamma=30.0, max_steps=10000, max_displacement=0.001)",
                "system.minimize_energy.minimize()"],1, wait = False)
#%%
server.request(f"system.integrator.run({10000})", [0,1])
# %%
import plotly.express as px
pos = server.request("system.part[:].pos", 0).T
q = server.request("system.part[:].q", 0).T
px.scatter_3d(x = pos[0], y = pos[1], z = pos[2], color=['cation' if q_==1 else 'anion' for q_ in q])

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
    def __init__(self, server, beta) -> None:
        self.server = server
        self.beta = beta
        self.server.request(["float(system.analysis.energy()['total'])",
                    "[list(system.part.select(q=-1).id), list(system.part.select(q=1).id)]",
                    "system.box_l"],[0,1], wait = False)
        self.server.wait_all()
        
        self.energy = [None]*2
        self.IDs = [None]*2
        self.box = [None]*2
        for i in range(2):
            self.energy[i], self.IDs[i], self.box[i] = self.server.responce(i)
        
        self.n_part = [len(self.IDs[0]), len(self.IDs[1])]
        self.vol = [float(np.prod(self.box[0])), float(np.prod(self.box[1]))]
        
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

            rnd_id_anion = random.choice(self.IDs[side][0])
            rnd_id_cation = random.choice(self.IDs[side][1])
            
            other_side = int(not(side))

            print(f"{side} -> {other_side}, {rnd_id_anion}{rnd_id_cation}")
            
            #remember removed pair position and velocity
            #then remove it and get new energy
            removed_anion_pos, removed_cation_pos, removed_anion_v, removed_cation_v, _, = server.request([
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
            #delta_F = -delta_S/self.beta


            if monte_carlo_accept(delta_F, self.beta):
                print('Move accepted')
                #store new state
                self.energy[side] = energy_after_removal
                self.energy[other_side] = energy_after_add
                
                self.IDs[side][0].remove(rnd_id_anion)
                self.IDs[side][1].remove(rnd_id_cation)
                self.IDs[other_side][0].append(add_anion_id)
                self.IDs[other_side][1].append(add_cation_id)
                
                self.n_part = [ len(self.IDs[0][0])+len(self.IDs[0][1]),
                                len(self.IDs[1][0])+len(self.IDs[1][1])]
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
mc = monte_carlo_charged_pairs(server, 1)
# %%
mc.IDs[0][0]
# %%