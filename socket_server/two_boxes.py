#%%
import time
from socket_server import SocketServer
import numpy as np
import random
import math

server = SocketServer('127.0.0.1', 10004)
server.start()
server.loop_thread().start()
#%%
import subprocess
clientA = subprocess.Popen(['python', 'espressomd_client.py'])
time.sleep(0.5)
clientB = subprocess.Popen(['python', 'espressomd_client.py'])
time.sleep(0.5)
# %%
server.send_message('\ECHO', server.addr_list[1])
server.send_message('\ECHO', server.addr_list[2])
# %%
#popululate first system with particles:
#for i in range(100):
#    server.send_message(
#        {'eval':[
#            "self.system.part.add(pos=self.system.box_l * np.random.random(3))",
#            ]
#        },
#    server.addr_list[2])
#    time.sleep(0.2)
for i in range(100):
    server.send_message('add_particle', server.addr_list[2])

#%%
server.send_message('n_particles', server.addr_list[2])

#%%
def monte_carlo_move():
    pass

# %%
def n_particles_and_energy():
    n_part=[None]*2
    energy=[None]*2
    
    server.send_message('n_particles', server.addr_list[1])
    time.sleep(0.1)
    n_part[0] = server.last_income.data
    server.send_message('n_particles', server.addr_list[2])
    time.sleep(0.1)
    n_part[1] = server.last_income.data
    time.sleep(0.1)
    server.send_message('get_total_energy', server.addr_list[1])
    time.sleep(0.1)
    energy[0] = server.last_income.data
    server.send_message('get_total_energy', server.addr_list[2])
    time.sleep(0.1)
    energy[1] = server.last_income.data
    time.sleep(0.1)
    
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

def monte_carlo_move():
    n_part, energy = n_particles_and_energy()
    rnd_part_n = random.randint(0,sum(n_part))
    print(f'particle number:{rnd_part_n}')
    side = 'left' if rnd_part_n < n_part[0] else 'right'
    if side == 'left':
        A = 1
        B = 2 
        print('Particle will be moved from the left box')
        server.send_message(
            {'eval':[
                f"self.system.part[{rnd_part_n}].pos",
                    ]
                }, server.addr_list[A])
        server.wait_clients_loop() 
        old_coord = server.last_income.data
        old_energy = float(sum(energy))
        print(f'old coord: {old_coord}')

        #remove from the left
        server.send_message(
            {'eval':[
                f"self.system.part[{rnd_part_n}].remove()",
                    ]
                }, server.addr_list[A])

        #put in the right
        server.send_message(
            {'eval':[
                f"self.system.part.add(pos=self.system.box_l * np.random.random(3)).id",
                    ]
                }, server.addr_list[B])
        server.wait_clients_loop()
        last_added_id= server.last_income.data
        print('The move is done')
        n_part, energy = n_particles_and_energy()
        if monte_carlo_accept(old_energy, float(sum(energy)), 1):
            print ('Move accepted')
        else:
            print ('Move declined')
            #remove from the right
            server.send_message(
                {'eval':[
                    f"self.system.part[{last_added_id}].remove()",
                        ]
                    }, server.addr_list[B])
            
            #put back to the left
            server.send_message(
            {'eval':[
                f"self.system.part.add(pos={old_coord})",
                    ]
                }, server.addr_list[A])
            server.wait_clients_loop() 
    else:
        print('Particle will be moved from the left box')
        rnd_part_n = rnd_part_n-n_part[0]
        A = 2
        B = 1 
        server.send_message(
            {'eval':[
                f"self.system.part[{rnd_part_n}].pos",
                    ]
                }, server.addr_list[A])
        server.wait_clients_loop() 
        old_coord = server.last_income.data
        old_energy = float(sum(energy))
        print(f'old coord: {old_coord}')

        #remove from the left
        server.send_message(
            {'eval':[
                f"self.system.part[{rnd_part_n}].remove()",
                    ]
                }, server.addr_list[A])

        #put in the right
        server.send_message(
            {'eval':[
                f"self.system.part.add(pos=self.system.box_l * np.random.random(3))",
                    ]
                }, server.addr_list[B])
        server.wait_clients_loop()
        last_added_id= server.last_income.data
        print('The move is done')
        n_part, energy = n_particles_and_energy()
        if monte_carlo_accept(old_energy, float(sum(energy)), 1):
            print ('Move accepted')
        else:
            print ('Move declined')
            #remove from the right
            server.send_message(
                {'eval':[
                    f"self.system.part[{rnd_part_n}].remove()",
                        ]
                    }, server.addr_list[B])
            
            #put back to the left
            server.send_message(
            {'eval':[
                f"self.system.part.add(pos={old_coord})",
                    ]
                }, server.addr_list[A])
            server.wait_clients_loop() 

def monte_carlo_accept(old_energy, new_energy, beta):
    delta_E = new_energy - old_energy
    if delta_E<0:
        return True
    else:
        prob = math.exp(-beta*delta_E)
        return (prob > random.random())
# %%
monte_carlo_move()
