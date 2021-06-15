#%%
from .Server2 import BaseSocketServer
from .Client2 import BaseClient
#%%
from Server2 import BaseSocketServer
from Client2 import BaseClient

import logging
import sys
logging.basicConfig(stream=open('log', 'w'), level=logging.DEBUG)

server = BaseSocketServer('127.0.0.1', 10000)
server.setup()
server.start()

client = BaseClient('127.0.0.1', 10000)
client.start_threads()
# %%
server.send(server.sockets_list[1], 'foo')
server.send(server.sockets_list[1], 'foo2')
# %%
client.send('hi',client.server_socket)
# %%
server.request(server.sockets_list[1], 'foo')