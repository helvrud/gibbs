#%%
import random
import math
import matplotlib.pyplot as plt
import seaborn
import numpy as np
import csv
import os
import sys
import subprocess
import pandas as pd
import socket_nodes
import tqdm
#os.chdir(sys.path[0])
import threading
from socket_nodes import Server
import logging
logging.basicConfig(stream=open('log_server', 'w'), level=logging.INFO)

PAIR = [0,1]
SIDES = [0,1]
#%%
#params
ELECTROSTATIC = False

V_all = 40**3*2
v = 0.5 #relative volume of the box with fixed anions

l_bjerrum = 2.0
temp = 1

N1 = 150
N2 = 50
N_anion_fixed = 10

#box volumes and dimmensions
V = [V_all*(1-v),V_all*v]
l = [V_**(1/3) for V_ in V]


###start server and nodes
server = socket_nodes.utils.create_server_and_nodes(
    scripts = ['esp_node.py', 'esp_node.py'], 
    args_list=[[str(l_)] for l_ in l], 
    python_executable = 'python')
#%%
subprocess.Popen(['python', 'esp_node.py','127.0.0.1',f'{server.PORT}', str(l[0])], stdout=open('log0', 'w'), stderr=open('log0err', 'w'))
server.wait_for_connections(1)
subprocess.Popen(['python', 'esp_node.py','127.0.0.1',f'{server.PORT}', str(l[1])], stdout=open('log1', 'w'))
server.wait_for_connections(2)

#%%
def populate_system(n1, n2, n_fixed):
    ##populate the systems##
    server(f"/populate({int(n1/2)}, type = 0, q = -1.0)", 0)
    server(f"/populate({int(n1/2)}, type = 1, q = +1.0)", 0)

    server(f"/populate({int(n2/2)}, type = 0, q = -1.0)", 1)
    server(f"/populate({int(n2/2)}, type = 1, q = +1.0)", 1)

    server(f"/populate({int(n_fixed)}, type = 2, q = -1.0)", 1)
    server(f"/populate({int(n_fixed)}, type = 1, q = +1.0)", 1)

populate_system(N1, N2, N_anion_fixed)
#%%
def setup_system():
    ##add LJ interactions and thermostats### 
    server(
            [
            "system.non_bonded_inter[0, 0].lennard_jones.set_params(epsilon=1, sigma=1, cutoff=3, shift='auto')",
            "system.non_bonded_inter[0, 1].lennard_jones.set_params(epsilon=1, sigma=1, cutoff=3, shift='auto')",
            "system.non_bonded_inter[1, 1].lennard_jones.set_params(epsilon=1, sigma=1, cutoff=3, shift='auto')",
            "system.non_bonded_inter[0, 2].lennard_jones.set_params(epsilon=1, sigma=1, cutoff=3, shift='auto')",
            "system.non_bonded_inter[1, 2].lennard_jones.set_params(epsilon=1, sigma=1, cutoff=3, shift='auto')",
            "system.non_bonded_inter[2, 2].lennard_jones.set_params(epsilon=1, sigma=1, cutoff=3, shift='auto')",
            "system.__setattr__('time_step', 0.001)",
            "system.cell_system.__setattr__('skin', 0.4)",
            "system.thermostat.set_langevin(kT=1, gamma=1, seed=42)",
            "system.minimize_energy.init(f_max=50, gamma=30.0, max_steps=10000, max_displacement=0.001)",
            "system.minimize_energy.minimize()"
            ], 
            [0,1]
        )

    ##switch on electrostatics
    if ELECTROSTATIC:
        server.request(f"system.actors.add(espressomd.electrostatics.P3M(prefactor={l_bjerrum * temp},accuracy=1e-3))",[0,1])

    #minimize energy and run md
    server([
                "system.minimize_energy.init(f_max=50, gamma=30.0, max_steps=10000, max_displacement=0.001)",
                "system.minimize_energy.minimize()",
                f"system.integrator.run({10000})"
                ],
                [0,1]
            )

setup_system()

#%%
class Monte_Carlo:
    @staticmethod
    def entropy_change(N1, N2, V1, V2, n=1):
        #N1, V1 - box we removing particle from
        #N2, V2 - box we adding to
        #n - number of particles 
        if n==1:
            return math.log((N1*V2)/((N2+1)*V1))
        elif n==2:
            return math.log((V2/V1)**2*(N1*(N1-1))/((N2+2)*(N2+1)))

    @staticmethod
    def accept(delta_fenergy, beta=1):
        if delta_fenergy<0:
            return True
        else:
            prob = math.exp(-beta*delta_fenergy)
            return (prob > random.random())

    def __init__(self) -> None:
        self.steps = 0
        request_body = [
            "/potential_energy()",
            "system.box_l",
            "/part_data(slice(None,None), ['id', 'type'])",
            ]
        system_init_state_request=server(request_body,SIDES)
        self.energy, self.box_l, part_dict= [
            [result.result()[i] for result in system_init_state_request] 
                for i in range(len(request_body))
                ]

        self.volumes = [float(np.prod(self.box_l[i])) for i in SIDES]
        
        for i,dict_ in enumerate(part_dict):
            dict_['side'] = i

        #save info about particles as pandas.DataFrame
        self.particles = pd.concat([
            pd.DataFrame(dict_) for dict_ in part_dict
            ], ignore_index=True)

        self._print_state()

    def _print_state(self):
        print('Energy:', self.energy)
        print('Volume:', self.volumes)
        print('Particles:')
        print(self.particles.groupby(by=['side', 'type']).size())
    
    def choose_side_and_part(self):
        side = random.choice([0,1])
        rnd_pair_indices = [
            random.choice(self.particles.query(f'side == {side} & type == {0}')['id'].to_list()), #anion
            random.choice(self.particles.query(f'side == {side} & type == {1}')['id'].to_list()) #cation
            ]
        return side, rnd_pair_indices
            
    def rotate_velocities_randomly(self,velocities):
        from scipy.spatial.transform import Rotation
        rot = Rotation.random().as_matrix
        velocities_rotated = [list(rot().dot(velocity)) for velocity in velocities]
        return velocities_rotated

    def move(self, side, pair_indices):
        other_side = int(not(side))
        
        ###Pair removal:##################################################
        #request to remove pair but store their pos and v
        #request.result will return [[part.id, part.pos, part.v], [part.id, part.pos, part.v]]
        attrs_to_return = {'id':'int', 'pos':'list', 'v':'list'}
        remove_part = server([
            f"/remove_particle({pair_indices[0]},{attrs_to_return})", #anion
            f"/remove_particle({pair_indices[1]},{attrs_to_return})", #cation
            ],side)
        #request to calculate energy, 
        #separated from previous one so we could do something else while executing
        energy_after_removal = server(
            "/potential_energy()"
            ,side)

        #rotate velocity vectors
        #can be done when remove_part request is done, 
        #note that energy_after_removal not necessarily should be done by now
        velocities = self.rotate_velocities_randomly(
            [remove_part.result()[i]['v'] for i in PAIR])


        ###Pair_addition###################################################
        #request to add pair and return assigned id then to calculate potential energy
        add_part = server([
                f"/add_particle(attrs_to_return=['id'], v={velocities[0]}, q = -1.0, type = 0)",#anion
                f"/add_particle(attrs_to_return=['id'], v={velocities[1]}, q = +1.0, type = 1)",#cation
                "/potential_energy()"#potential energy
            ], other_side)

        
        ###Energy change###################################################
        E = [energy_after_removal.result(),add_part.result()[-1]]#-1-last result

        #number of particles excluding fixed
        n_parts = self.particles.loc[self.particles.type!=2].groupby(by='side').size()

        n1 = n_parts[side]; n2 = n_parts[other_side]
        v1 = self.volumes[side]; v2 = self.volumes[other_side]
        delta_S = Monte_Carlo.entropy_change(n1,n2,v1,v2,2)
        
        #delta_F = -delta_S ##IDEAL GAS
        delta_F = sum(E) - sum(self.energy) - delta_S 
        

        ###All the data needed to reverse the move################################
        reversal_data =  {
            'removed': remove_part.result()[0:2],
            'added' : add_part.result()[0:2],
            'side' : side}

        #return data that we can reverse or update the system state with
        return reversal_data, E, delta_F

    def reverse_move(self, reversal_data):
        side = reversal_data['side']
        other_side = int(not(side))
        reverse_remove = server([
            f"/add_particle(['id'], q = -1.0, type = 0, **{reversal_data['removed'][0]})",
            f"/add_particle(['id'], q = +1.0, type = 1, **{reversal_data['removed'][1]})"
            ], side)
        
        reverse_add = server([
            f"/remove_particle({reversal_data['added'][0]['id']},['id'])", #anion
            f"/remove_particle({reversal_data['added'][1]['id']},['id'])", #cation
            ], other_side)

    def update_state(self, reversal_data, E):
        side = reversal_data['side']
        other_side = int(not(side))
        
        ###Update removed#########################################
        #can be done much easier
        find = lambda _, side, ids: (_.side==side)&(_.id == ids)
        idx_to_drop = [
            self.particles.loc[
                find(
                    self.particles, side, reversal_data['removed'][i]['id']
                    )].index[0] for i in PAIR]
        self.particles.drop(idx_to_drop, inplace=True)
        ######Update added########################################
        added = pd.DataFrame(reversal_data['added'])
        added['side'] = other_side
        added['type'] = [0,1]
        self.particles = self.particles.append(
            added,
            ignore_index=True, verify_integrity=True
            )
        ######Update energy#######################################
        mc.energy = E
        
    def step(self):
        side, pair_indices = self.choose_side_and_part()
        reversal_data, E, delta_F = self.move(side, pair_indices)
        if side:
            print(f"Move: -> ", end = ' ')
        else:
            print(f"Move: <- ", end = ' ')
        print (f"delta_F: {delta_F},",end = ' ')
        if Monte_Carlo.accept(delta_F,1):
            print('accepted')
            self.update_state(reversal_data, E)
        else:
            print('rejected')
            self.reverse_move(reversal_data)
        print(*self.particles.groupby(by='side').size(), sep=' | ')
        self.steps+=1
    
def run(mc, warmup_steps):#, sample_size, n_samples):
    res_df = pd.DataFrame()
    n_part_acc = []
    energy_acc = []
    for i in range(warmup_steps):
        mc.step()
        part_info = pd.DataFrame(mc.particles.groupby(by=['side', 'type']).size(), columns = ['n'])
        part_info['step'] = mc.steps
        part_info.set_index(keys=['step'], append = 'True').reorder_levels(['step','side','type'])
        res_df=res_df.append(part_info)
    return res_df
            


        
#%%
mc = Monte_Carlo()
#%%
mc.step()
# %%
mc._print_state()
# %%
socket_nodes.utils.__dir__()
# %%
