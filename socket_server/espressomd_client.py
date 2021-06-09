#%%
import sys
import espressomd
import numpy as np

from socket_server import Client

box = np.array([10, 10, 10])
system = espressomd.System(box_l=box)
system.time_step = 0.0005
system.cell_system.set_domain_decomposition(use_verlet_lists=True)
system.cell_system.skin = 0.4

system.non_bonded_inter[0, 0].lennard_jones.set_params(
    epsilon=1.0, sigma=1.0,
    cutoff=3.0, shift="auto")
#%%
class EspressoClient(Client):
    system = None
    last_added = None
    #method eval has to be overridden, 
    #so that you can use import from this script
    #otherwise you will get NameError trying to eval(np.*)
    def eval(self, eval_str):
        result = eval(eval_str)
        return result
    
    def add_particle(self):
        self.last_added = self.system.part.add(pos=self.system.box_l * np.random.random(3)).id

    def remove_last_added(self):
        self.system.part[self.last_added].remove()
    
    def get_total_energy(self):
        return float(self.system.analysis.energy()['total'])

    def n_particles(self):
        return int(len(self.system.part[:]))

    def _income_host_message_handle(self, msg):
        super()._income_host_message_handle(msg)
        data = msg.data
        if isinstance(data, str) and (data[0]!='\\'):
            try:
                result = getattr(self, data)()
            except Exception as e:
                result = e
            try:
                self.send_message(result, 'host')
            except:
                self.send_message('Result can not be serialized', 'host')
                
client = EspressoClient('127.0.0.1', 10004)
client.system = system
#%%
client.connect()
client.loop()
# %%
