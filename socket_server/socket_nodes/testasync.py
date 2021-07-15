# %%
from Terminal import BaseTerminal, RequestStatus
terminal = BaseTerminal('127.0.0.1', 10000)
terminal.setup()
import threading
threading.Thread(target=terminal.loop_forever, daemon=True).start()
# %%
%%time
results = []
for i in range(100):
    results.append(terminal.request(f'sleep(0.1)', 0))
    results.append(terminal.request(f'{i}', 0))

# %%
results[99].result()
# %%
terminal.request(f'{True}', 0).result()
# %%
