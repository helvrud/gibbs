#%%
from time import sleep
from Terminal import BaseTerminal
from Node import BaseNode
#%%
terminal = BaseTerminal('127.0.0.1', 10000)
terminal.setup()
import threading
threading.Thread(target=terminal.loop_forever, daemon=True).start()
# %%
node = BaseNode('127.0.0.1', 10000) 
node.start()
# %%
request1 = terminal.request('True', 0)
request2 = terminal.request('sleep(2)', 0)
# %%
print(request1.result())
print(request2.result())
print(request1.result())
# %%
for i in range(100):
    print(terminal.request(f'{i}', 0).result())
