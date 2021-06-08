#%%
import time
from socket_server import SocketServer

server = SocketServer('127.0.0.1', 10001)
server.start()
server.loop_thread().start()
#%%
import subprocess
clientA = subprocess.Popen(['python', 'espressomd_client.py'])
time.sleep(0.5)
#clientB = subprocess.Popen(['python', 'espressomd_client.py'])
#time.sleep(0.5)
#%%
server.send_message(
    {'eval':[
        "self.system.cell_system.skin",
            ]
        }, 
    server.addr_list[1])
# %%
server.send_message('\ECHO', server.addr_list[1])
#server.send_message('\ECHO', server.addr_list[2])
# %%
server._active=False
# %%
server._stop_server_routine()
# %%
server.addr_list
# %%
