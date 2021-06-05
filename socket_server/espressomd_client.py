#%%
from typing import Dict
import espressomd
import numpy as np

required_features = ["LENNARD_JONES"]
espressomd.assert_features(required_features)

box = [40, 30, 20]
system = espressomd.System(box_l=box)

# %%
from socket_server import Interface, SocketServer

server = SocketServer('127.0.0.1', 10001)
server.start()
server.loop_thread().start()
#%%
client = Interface('127.0.0.1', 10001, system)
client.connect()
# %%
client.loop_thread().start()
# %%
server.send_message('hello', client.addr)
# %%
server.send_message({"SET" : ("cell_system.skin", 0.4)}, client.addr)
#%%
server.send_message({"SET" : (
        "non_bonded_inter[0, 0].lennard_jones.set_params",
        dict(epsilon=100.0, sigma=1.0, cutoff=3.0, shift="auto")
        )
    },
    client.addr)
# %%
client._object.non_bonded_inter[0, 0].lennard_jones.get_params()
# %%
client._object.non_bonded_inter[0, 0].lennard_jones.set_params()