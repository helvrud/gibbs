#%%
import threading
import subprocess
from socket_nodes import Server


#%%
server = Server('127.0.0.1', 0)
threading.Thread(target=server.run, daemon=True).start()
# %%
subprocess.Popen(['python', 'example_node.py', '127.0.0.1', f'{server.PORT}'])
subprocess.Popen(['python', 'example_node.py', '127.0.0.1', f'{server.PORT}'])
server.wait_for_connections(2)

# %%
request = []
for i in range(100):
    request.append(server(f'{i}', 0))
    request.append(server(f'{i}**2', 1))
# %%
print ([request_.result() for request_ in request])
# %%
