#%%
import threading
import subprocess
from socket_nodes import Server
import socket_nodes.utils


server = socket_nodes.utils.create_server_and_nodes(
    scripts = ['example_node.py', 'example_node.py'], 
    args_list=[[],[]], 
    python_executable = 'python')

# %%
request = []
for i in range(100):
    request.append(server(f'{i}', 0))
    request.append(server(f'{i}**2', 1))
# %%
print ([request_.result() for request_ in request])
# %%
server.nodes
# %%
