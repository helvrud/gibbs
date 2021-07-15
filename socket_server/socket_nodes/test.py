#%%
#import asyncio
#import patch_asyncio
from time import sleep
from Terminal import BaseTerminal
from ExecutorNode import BaseExecutorNode as Node
import subprocess
#%%
terminal = BaseTerminal('127.0.0.1', 0)
terminal.setup()
PORT = terminal.socket.getsockname()[1]
print("PORT: ", PORT)
import threading
threading.Thread(target=terminal.run, daemon=True).start()
# %%
subprocess.Popen(['python', 'ExecutorNode.py', '127.0.0.1', f'{PORT}'])
while len(terminal.nodes)==0:
    pass
# %%
request1 = terminal.request('True', 0)
request2 = terminal.request('system.box_l', 0)
request3 = terminal.request('25**5', 0).result()
# %%
print(request2.result())
print(request3)
print(request1.result())
# %%
%%time
for i in range(100):
    result = terminal.request('system.box_l', 0)
result.result()
# %%
