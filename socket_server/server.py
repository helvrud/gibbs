#%%
from socket_server import SocketServer

server = SocketServer('127.0.0.1', 10007)
server.start()
server.loop_thread().start()
#%%
import subprocess
clientA = subprocess.Popen(['python', 'espresso_client_2.py'])
#%%
server.addr_list
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

#%%
server.send_message(
    {'eval':[
        "self.system.part.add(pos = [0,0,0])",
        ]
    },
    server.addr_list[1])
# %%
server.send_message(
        {'eval':[
            "self.system.part[:].pos",
            ]
        },
        server.addr_list[1])
# %%
server.last_message.data
# %%
clientA.poll()
# %%
