#%%
import logging
from os import wait
import sys
logging.basicConfig(stream=open('log', 'w'), level=logging.DEBUG)

from socket_server import Server

server = Server('127.0.0.1', 10001)
server.setup()
server.start()
#%%
import subprocess
clientA = subprocess.Popen(['python', 'esp_client.py'])
clientB = subprocess.Popen(['python', 'esp_client.py'])
# %%
for i in range(100):
    server.request("self.system.part.add(pos=self.system.box_l * np.random.random(3))", 1, wait = False)
server.request("len(self.system.part[:])", 1)
# %%
