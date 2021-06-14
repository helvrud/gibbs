#%%
import time
from socket_server import SocketServer

server = SocketServer('127.0.0.1', 10011)
server.setup()
p1 = server.start()

#%%
import subprocess
clientA = subprocess.Popen(['python', 'espressomd_client.py'])
time.sleep(1)
#%%
server.send_message(
    {'eval':[
        "self.system.cell_system.skin",
            ]
        }, 
    server.addr_list[1])
# %%
server.send_message(
    {'eval':[
        "self.system.cell_system.__setattr__('skin', 0.4)",
        "self.system.__setattr__('time_step', 0.0005)",
        "self.system.cell_system.set_domain_decomposition(use_verlet_lists = True)"
            ]
        }, 
    server.addr_list[1])
time.sleep(1)
#%%
server.send_message(
    {'eval':[
        "self.system.part.add(pos = np.array([1.8,0,2]))",
        ]
    },
    server.addr_list[1])
#%%
server.send_message(
        {'eval':[
            "self.system.part[:].pos",
            ]
        },
        server.addr_list[1])
time.sleep(1)
# %%
server.send_message('\ECHO', server.addr_list[1])
# %%
server._active=False
# %%
server.addr_list
# %%
server._stop_server_routine()
