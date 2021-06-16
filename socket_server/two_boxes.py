#%%
import random
import math
import numpy as np

#import logging
#logging.basicConfig(stream=open('log', 'w'), level=logging.DEBUG)

from socket_server import Server

server = Server('127.0.0.1', 10000)
server.setup()
server.start()

import subprocess
clientA = subprocess.Popen(['python', 'esp_client.py'])
clientB = subprocess.Popen(['python', 'esp_client.py'])

#wait for clients to connect
while len(server.addr_list)<3:
    pass

#populate one of the boxes
for i in range(100):
    server.request("self.system.part.add(pos=self.system.box_l * np.random.random(3))", 1, wait = False)
server.request("len(self.system.part[:])", 1)

def get_energy():
    server.request("self.system.analysis.energy()['total']",0, wait = False)
    server.request("self.system.analysis.energy()['total']",1, wait = False)
    server.wait_all()
    energy = [  
        float(server.responce(0)),
        float(server.responce(1))
        ]
    return energy

def particle_pos(id, n) -> list:
    pos = list(server.request(f"self.system.part[{id}].pos",n))
    return pos

def remove_particle(id, n):
    server.request(f"self.system.part[{id}].remove()",n, wait=False)

def add_particle(n, pos = None) -> int:
    if pos is None:
        id = int(server.request(
            "self.system.part.add(pos=self.system.box_l * np.random.random(3)).id",
            n
            ))
    else:
        id = int(server.request(
            f"self.system.part.add(pos={pos}).id",
            n
            ))
    return id

def number_of_particles():
    server.request("len(self.system.part[:])", 0, wait = False)
    server.request("len(self.system.part[:])", 1, wait = False)
    server.wait_all()
    n_part = [
        int(server.responce(0)),
        int(server.responce(1))
    ]
    return n_part

def get_ids():
    server.request("self.system.part[:].id", 0, wait = False)
    server.request("self.system.part[:].id", 1, wait = False)
    server.wait_all()
    ids = [
        list(server.responce(0)),
        list(server.responce(1))
    ]
    return ids

def rnd_particle_id():
    ids = get_ids()
    n_part = [len(x) for x in ids]
    side = int(random.random() > n_part[0]/sum(n_part))
    rnd_id = random.choice(ids[side])
    return (side, rnd_id, n_part)

def monte_carlo_accept(old_energy, new_energy, beta):
    delta_E = new_energy - old_energy
    if delta_E<0:
        return True
    else:
        prob = math.exp(-beta*delta_E)
        return (prob > random.random())

#%%
def monte_carlo_move(beta, agg):
    old_energy = get_energy()
    
    #pick random box and particle
    sideA, part_id, n_part = rnd_particle_id()

    agg.append(n_part)

    old_pos = particle_pos(part_id, sideA)
    remove_particle(part_id, sideA)

    #the other box
    sideB = int(not(sideA))
    moved_part = add_particle(sideB)

    new_energy = get_energy()

    if monte_carlo_accept(sum(old_energy), sum(new_energy), beta):
        #print('Move accepted')
        pass

    else:
        #print('Move rejected')
        #reverse the move
        remove_particle(moved_part, sideB)
        add_particle(sideA, old_pos)

# %%
plot_arr = []
#%%
%%time
for i in range(100):
    monte_carlo_move(beta = 1, agg = plot_arr)
#%%
import matplotlib.pyplot as plt

Y = np.array(plot_arr).T

plt.plot(Y[0])
plt.plot(Y[1])
plt.show()
# %%
