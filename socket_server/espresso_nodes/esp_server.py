#%%
import threading
import subprocess
from socket_nodes import Server

#%%
server = Server('127.0.0.1', 0)
threading.Thread(target=server.run, daemon=True).start()
# %%
subprocess.Popen(['python', 'esp_node.py', '127.0.0.1', f'{server.PORT}', '10'])
subprocess.Popen(['python', 'esp_node.py', '127.0.0.1', f'{server.PORT}', '10'])
server.wait_for_connections(2)
# %%
request = server(f'system.box_l', 0)
# %%
request.result()
# %%
