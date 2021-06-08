#%%
import espressomd
import numpy as np
box = [40, 30, 20]
system = espressomd.System(box_l=box)
from socket_server import Client
client = Client('127.0.0.1', 10000)
client.system = system
client.connect()
client.loop()
# %%
