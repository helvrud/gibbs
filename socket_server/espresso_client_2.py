#%%
import espressomd
import numpy as np
box = [40, 30, 20]
system = espressomd.System(box_l=box)
from socket_server import Client
client = Client('127.0.0.1', 10007)
client.system = system
#%%
client.connect()
client.loop_thread().start()
# %%
#client.eval("self.system.part.add(pos = [0,0,0])")
# %%
from socket_server import SocketServer

server = SocketServer('127.0.0.1', 10007)
server.start()
server.loop_thread().start()
# %%
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

# %%
server.send_message(
    {'eval':[
        "self.system.part.add(pos = [1,1,1])",
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
msg= client.eval("self.system.part.add(pos = numpy.array([1,1,1]))")
# %%
client.send_message(msg, 'host')
# %%
server.last_message.data
# %%
