#%%
import threading
import subprocess
from socket_nodes import Server
import os
import sys
#os.chdir(sys.path[0]) #comment if run interactively

#%%
#init server, PORT assigned by OS
server = Server('127.0.0.1', 0)
#non-blocking server loop
threading.Thread(target=server.run, daemon=True).start()
# %%
#start two nodes in subprocesses
subprocess.Popen(['python', 'esp_node.py', '127.0.0.1', f'{server.PORT}', '10'])
subprocess.Popen(['python', 'esp_node.py', '127.0.0.1', f'{server.PORT}', '10'])
#wait them to connect
server.wait_for_connections(2)
# %%
#arbitrary function
request = server(f'system.box_l', 0)
print(request.result())

#user-defined function
server(f"/populate({10}, type = 0, q = -1.0)", 0)

request = server(f'len(system.part[:])', 0)
request.result()# has to be 10

