#%%
import random
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
    def pick_rnd_id(self):
        ids = self.system.part[:].id
        return random.choice(ids)

    def eval(self, eval_str):
        result = eval(eval_str)
        return result
    
    def add_rnd_particle(self):
        self.last_added = self.system.part.add(pos=self.system.box_l * np.random.random(3)).id

    def add_particle(self, pos):
        self.last_added = self.system.part.add(pos=pos).id

    def remove_particle(self, id):
        self.system.part[id].remove()

    def remove_last_added(self):
        self.system.part[self.last_added].remove()

    def get_particle_pos(self, id):
        return self.system.part[id].pos

    def get_total_energy(self):
        return float(self.system.analysis.energy()['total'])

    def n_particles(self):
        return int(len(self.system.part[:]))

    def _income_host_message_handle(self, msg):
        super()._income_host_message_handle(msg)
        data = msg.data
        if isinstance(data, tuple):
            try:
                if len(data) ==1:
                    result = getattr(self, data[0])()
                else:
                    result = getattr(self, data[0])([1])
            except Exception as e:
                result = e
            try:
                self.send_message(result, 'host')
            except:
                self.send_message('Result can not be serialized', 'host')
                
client = EspressoClient('127.0.0.1', 10011)
client.system = system
#%%
client.connect()
client.loop()