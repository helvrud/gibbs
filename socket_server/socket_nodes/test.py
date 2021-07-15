#%%
import asyncio
from time import sleep
from Terminal import BaseTerminal
#from ExecutorNode import BaseExecutorNode as Node
from Node import BaseNodeAsync as Node
#%%
terminal = BaseTerminal('127.0.0.1', 10001)
terminal.setup()
import threading
threading.Thread(target=terminal.loop_forever, daemon=True).start()
# %%
node = Node('127.0.0.1', 10001) 
asyncio.get_event_loop().create_task(node.main())
# %%
request1 = terminal.request('True', 0)
request2 = terminal.request('sleep(2)', 0)
# %%
print(request1.result())
print(request2.result())
print(request1.result())
# %%
#%%
from Node import AsyncEchoNode
node = AsyncEchoNode('127.0.0.1', 10001)
node.run()
#%%

request = terminal.request(f'True', 0)
request.result()
# %%
