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
clientA = subprocess.Popen(['/home/ml/espresso/build/pypresso', 'esp_client.py'])
clientB = subprocess.Popen(['/home/ml/espresso/build/pypresso', 'esp_client.py'])

#wait for clients to connect
while len(server.addr_list)<3:
    pass

#populate one of the boxes
for i in range(100):
    server.request("self.system.part.add(pos=self.system.box_l * np.random.random(3))", 1, wait = False)
server.request("len(self.system.part[:])", 1)

server.request("self.system.minimize_energy.init(f_max=50, gamma=30.0, max_steps=10000, max_displacement=0.001)", 1)
server.request("self.system.minimize_energy.minimize()", 1)
server.request("system.cell_system.tune_skin(0.1, 4.0, 1e-1, 1000)", 1)

server.request("self.system.thermostat.set_langevin(kT=1, gamma=1, seed=42)",0, wait = False)
server.request("self.system.thermostat.set_langevin(kT=1, gamma=1, seed=42)",1, wait = False)
#%%
def md(n, steps : int):
    server.request(f"system.integrator.run({steps})", n)


def get_energy():
    server.request("self.system.analysis.energy()",0, wait = False)
    server.request("self.system.analysis.energy()",1, wait = False)
    server.wait_all()
    energy = [  
        server.responce(0),
        server.responce(1)
        ]
    energy = [  
        float(energy[0]['total'] - energy[0]['kinetic']),
        float(energy[1]['total'] - energy[1]['kinetic'])
        ]
    return energy

def get_volume():
    server.request("self.system.box_l",0, wait = False)
    server.request("self.system.box_l",1, wait = False)
    server.wait_all()
    volumes = [
        float(np.prod(server.responce(0))),
        float(np.prod(server.responce(0)))
    ]
    return volumes

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
    #side = int(random.random() > n_part[0]/sum(n_part))
    side = random.randint(0,1)
    rnd_id = random.choice(ids[side])
    return (side, rnd_id, n_part)

def monte_carlo_accept(old_energy, new_energy, entropy_change, beta):
    delta_E = new_energy - old_energy - entropy_change
    if delta_E<0:
        return True
    else:
        prob = math.exp(-beta*delta_E)
        return (prob > random.random())

def delta_S(V : float, N : float, dN : int) -> float:
    if dN ==-1:
        return math.log(N/V)
    elif dN == 1:
        return math.log(V/(N+1))

#%%
volumes = get_volume()
def monte_carlo_move(beta, agg1, agg2, agg3):
    old_energy = get_energy()
    agg2.append(old_energy)
    
    #pick random box and particle
    sideA, part_id, n_part = rnd_particle_id()
    agg1.append(n_part)

    old_pos = particle_pos(part_id, sideA)
    remove_particle(part_id, sideA)

    #the other box
    sideB = int(not(sideA))
    moved_part = add_particle(sideB)

    new_energy = get_energy()

    sideA = 1
    _dir = -1 if (sideA == 0) else +1
    entropy_change = [
        delta_S(volumes[0], n_part[0], _dir),
        delta_S(volumes[1], n_part[1], -_dir)
    ]

    agg3.append(entropy_change)

    if monte_carlo_accept(sum(old_energy), sum(new_energy), sum(entropy_change), beta):
        print('Move accepted')
        pass

    else:
        print('Move rejected')
        #reverse the move
        remove_particle(moved_part, sideB)
        add_particle(sideA, old_pos)
    print(n_part)

# %%
plot_arr = []
energy = []
entropy = []
#%%
for j in range(1):
    for i in range(100):
        monte_carlo_move(beta = 1, agg1 = plot_arr, agg2 = energy, agg3 = entropy)
    #md(1, 100)
#%%
import matplotlib.pyplot as plt

Y = np.array(plot_arr).T

plt.plot(Y[0])
plt.plot(Y[1])
plt.show()
#%%
Y = np.array(energy).T

plt.plot(Y[0])
plt.plot(Y[1])
plt.show()
# %%
#Y = np.cumsum(np.array(entropy).T, axis = 1)

Y = np.array(entropy).T

plt.plot(Y[0])
plt.plot(Y[1])
plt.show()

# %%
