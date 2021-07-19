#%%
import threading
import subprocess
from libserver import Server
#import logging
#logging.basicConfig(stream=open('log', 'w'), level=logging.DEBUG)
#%%
terminal = Server('127.0.0.1', 10000)
PORT = terminal.socket.getsockname()[1]
print("PORT: ", PORT)
threading.Thread(target=terminal.run, daemon=True).start()
# %%
subprocess.Popen(['python', 'example_node.py', '127.0.0.1', f'{PORT}'])
#%%
subprocess.Popen(['python', 'example_node.py', '127.0.0.1', f'{PORT}'])
# %%
request = []
for i in range(100):
    request.append(terminal.request(f'{i}', [0,1]))
    #request.append(terminal.request(f'sleep(0.1)', 1))
# %%
print ([request_.result() for request_ in request])

# %%
