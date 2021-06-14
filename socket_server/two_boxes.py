#%%
import time
from socket_server import SocketServer
import numpy as np
import random
import math

server = SocketServer('127.0.0.1', 10012)
server.setup()
server.start()
time.sleep(0.5)
import subprocess
clientA = subprocess.Popen(['python', 'espressomd_client.py'])
time.sleep(0.5)
clientB = subprocess.Popen(['python', 'espressomd_client.py'])
time.sleep(0.5)
# %%
#popululate first system with particles:
for i in range(100):
    server.send_request(('add_rnd_particle',), server.addr_list[2])

#%%
server.send_request(('n_particles',), server.addr_list[2])

# %%
def n_particles_and_energy(print_ = False):
    n_part=[None]*2
    energy=[None]*2
    
    n_part[0] =  server.send_request(('n_particles',), server.addr_list[1])
    
    n_part[1] = server.send_request(('n_particles',), server.addr_list[2])
    

    
    energy[0] = server.send_request(('get_total_energy',), server.addr_list[1])
    
    energy[1] = server.send_request(('get_total_energy',), server.addr_list[2])
    
    if print_:
        print()
        print('-'*80)
        print('n particles')
        print(f'boxA : {n_part[0]}  boxB : {n_part[1]}')
        print('energy')
        print(f'boxA : {energy[0]}  boxB : {energy[1]}')
        print('-'*80)
        print()

    return n_part, energy
# %%
n_particles_and_energy(True)

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
    rnd_part_n = random.randint(0,100)
    side = 'left' if rnd_part_n < n_part[0] else 'right'
    _A = server.addr_list[1]
    _B = server.addr_list[2]
    def move(A,B):
        rnd_id = server.send_request(('pick_rnd_id',), A)
        print(f'particle number:{rnd_id}')
        
        posA = server.send_request(
                {'eval':[
                    f"self.system.part[{rnd_id}].pos",
                    ]
                },
            A)
        posA= list(posA)
        
        server.send_request(
                {'eval':[
                    f"self.system.part[{rnd_id}].remove()",
                    ]
                },
            A)


        part_added_to_B = server.send_request(
                {'eval':[
                    f"self.system.part.add(pos=self.system.box_l * np.random.random(3)).id",
                    ]
                },
            B)
        
        old_energy = sum(energy)

        n_part_new, energy_new = n_particles_and_energy(True)


        if monte_carlo_accept(old_energy, sum(energy_new), 1):
            print('Move accepted')
        
        else:
            print('Move rejected')
            server.send_request(
                {'eval':[
                    f"self.system.part[{part_added_to_B}].remove()",
                    ]
                },
            B)
            
            #server.send_request(('add_particle', posA), A)

            server.send_request(
                {'eval':[
                    f"self.system.part.add(pos={posA}).id",
                    ]
                },
            A)
        print('')
        print('')
        print('')
        print('')
    
    if side == 'left':
        print('Particle will be moved from A to B box')
        move(_A,_B)
    else:
        print('Particle will be moved from B to A box')
        move(_B,_A)
# %%
try:
    monte_carlo_move()
except:
    pass
#%%
for i in range(100):
    monte_carlo_move()

# %%
