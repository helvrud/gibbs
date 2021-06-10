#%%
import time
from socket_server import SocketServer
import numpy as np
import random
import math

server = SocketServer('127.0.0.1', 10011)
server.setup()
server.start()
time.sleep(0.2)
import subprocess
clientA = subprocess.Popen(['python', 'espressomd_client.py'])
time.sleep(0.2)
clientB = subprocess.Popen(['python', 'espressomd_client.py'])
time.sleep(0.2)
# %%
server.send_message('\ECHO', server.addr_list[1])
#%%
server.send_message('\ECHO', server.addr_list[2])
# %%
#popululate first system with particles:
for i in range(100):
    server.send_message(('add_rnd_particle',), server.addr_list[2])
    time.sleep(0.02)

#%%
server.send_message(('n_particles',), server.addr_list[2])

# %%
def n_particles_and_energy():
    n_part=[None]*2
    energy=[None]*2
    
    server.send_message(('n_particles',), server.addr_list[1])
    time.sleep(0.5)
    n_part[0] = server.last_income.data
    server.send_message(('n_particles',), server.addr_list[2])
    time.sleep(0.5)
    n_part[1] = server.last_income.data
    time.sleep(0.5)
    server.send_message(('get_total_energy',), server.addr_list[1])
    time.sleep(0.5)
    energy[0] = server.last_income.data
    server.send_message(('get_total_energy',), server.addr_list[2])
    time.sleep(0.5)
    energy[1] = server.last_income.data
    time.sleep(0.5)
    
    print()
    print('-'*80)
    print('n particles')
    print(f'box0 : {n_part[0]}  box1 : {n_part[1]}')
    print('energy')
    print(f'box0 : {energy[0]}  box1 : {energy[1]}')
    print('-'*80)
    print()

    return n_part, energy
# %%
n_particles_and_energy()

#%%
def monte_carlo_accept(old_energy, new_energy, beta):
    delta_E = new_energy - old_energy
    if delta_E<0:
        return True
    else:
        prob = math.exp(-beta*delta_E)
        return (prob > random.random())
def monte_carlo_move():
    n_part, energy = n_particles_and_energy()
    rnd_part_n = random.randint(0,sum(n_part))
    side = 'left' if rnd_part_n < n_part[0] else 'right'
    def move(A,B):
        print(f'particle number:{rnd_part_n}')
        server.send_message(('get_particle_pos', rnd_part_n), A)
        time.sleep(0.5)
        posA=server.last_income

        server.send_message(('remove_particle', rnd_part_n), A)
        
        server.send_message(('add_rnd_particle',), B)

        old_energy = sum(energy)

        n_part_new, energy_new = n_particles_and_energy()

        if monte_carlo_accept(old_energy, sum(energy_new), 1):
            print('Move accepted')
        
        else:
            print('Move rejected')
            server.send_message(('remove_last_added',), B)
            server.send_message(('add_particle', posA), A)
    if side == 'left':
        print('Particle will be moved from A to B box')
        A = server.addr_list[1]
        B = server.addr_list[2]
        move(A,B)
    else:
        rnd_part_n = rnd_part_n - n_part[0]
        print('Particle will be moved from B to A box')
        A = server.addr_list[2]
        B = server.addr_list[1]
        move(A,B)
# %%
monte_carlo_move()

# %%
server.addr_list[1]
# %%
# %%
