#%%
import asyncio
import threading
def isnotebook():
    try:
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':
            return True   # Jupyter notebook or qtconsole
        elif shell == 'TerminalInteractiveShell':
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)
    except NameError:
        return False      # Probably standard Python interpreter
if isnotebook():
    import nest_asyncio
    nest_asyncio.apply()
    print("Interaction environment notified.\n Asyncio patched!")
else:
    print("Python interpreter notified.\n Asyncio not patched!")
import time

#%%
class AsyncTest:
    async def count(self, i : int):
        for j in range(i):
            print(j)
            await asyncio.sleep(0.0001)

    async def say_hi(self, i : int):
        for j in range(i):
            print('hi')
            await asyncio.sleep(0.0002)

    
    async def event_loop(self):
        print('main')
        await asyncio.gather(self.count(10),self.say_hi(10))

    def main(self):
        asyncio.run(self.event_loop())

class ThreadTest:
    def count(self, i : int):
        for j in range(i):
            print(j)
            time.sleep(0.0001)

    def say_hi(self, i : int):
        for j in range(i):
            print('hi')
            time.sleep(0.0002)

    def main(self):
        t1 = threading.Thread(target=self.count(10))
        t2 = threading.Thread(target=self.say_hi(10))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

# %%
test = AsyncTest()
#test = ThreadTest()
# %%
test.main()
# %%
