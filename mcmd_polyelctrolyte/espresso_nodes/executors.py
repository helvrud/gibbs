"""
Espresso node - espresso instance ready to reply to a request if one received with TCP socket,
the node is listening to the socket it connected to and send back replies. It is situated on the client side of the socket.

The node will delegate the execution to the the instance of the socket_nodes.Executor class.
So to create a node one has to instantiate an executor object of the Executor class.

Here we inherit socket_nodes.LocalScopeExecutor to create EspressoExecutorSalt and EspressoExecutorGel classes.
In the child classes we define functions that will be exposed to the server (monte carlo script).
"""
#%%
from socket_nodes import LocalScopeExecutor

##import all you might need later when requesting from server
import espressomd
from espressomd import electrostatics
import numpy as np

#auto sampling routine are the same as in montecarlo one
from montecarlo import sample_to_target_error

class EspressoExecutorSalt(LocalScopeExecutor):
    ###########overridden base class functions #############
    def __init__(self, espresso_system_instance) -> None:
        super().__init__()
        #if 'system' not in globals():
        #    raise(RuntimeError('espressomd.System is not initialized'))
        #else:
        #    self.system = espresso_system_instance
        self.system = espresso_system_instance

    ###########'private' user defined function #############
    #the next functions will not be exposed to eval() and thus can be requested to evaluate
    #they are used only within the class

    @staticmethod
    def __type_cast(type_names_dict) -> dict:
        """
        the function converts dictionary like
        {'a' : 'int', 'b' : 'float'} to {'a' : int, 'b' : float}
        note that here 'int' from string is converted to a function int

        motivation:
        we can not send the function over the socket, so we send a string
        sometimes we want to cast the result to some type,
        the type we want to cast the result to has to be defined as a string
        """
        return {k : eval(f'{v}') for k, v in type_names_dict.items()}

    def __get_particles(self, indices):
        """
        selects some particles based on the type of indices
        """
        # one particle selection
        if isinstance(indices, int):
            particles = [self.system.part[indices]]
        # selection by slice object
        elif isinstance(indices, slice):
            particles = self.system.part[indices]
        # (a,b) -> slice(a,b)
        elif isinstance(indices, tuple):
            particles = self.system.part[slice(*indices)]
        # select by the indices provided in list,
        # note that [5,10] select only 5th and 10th particle, not the range
        elif isinstance(indices, list):
            particles = [self.system.part[id] for id in indices]
        else:
            raise TypeError('system.part[indices] indices type error')
        return particles

    def __get_and_cast_attributes(self, iterable, attrs):
        """
        Providing some iterable (particles in the most cases),
        the method collect and cast the attributes values into a list or a dictionary

        example:
        particles = system.part[0:3]
        __get_and_cast_attributes(self, particles, ['id', 'type']) -> [[0, 0], [1,0], [2,0]]
        __get_and_cast_attributes(self, particles, {'id':'int', 'pos':'list'}) -> [[0, [0.25,0.53,0.23]], [1,[0.67,0.4,0.01]], [2,[0.45,0.33,0.765]]]
        """
        if isinstance(attrs, list):
            result = [{
                attr : getattr(item, attr)
                for attr in attrs
                } for item in iterable]
        elif isinstance(attrs, dict):
            cast = EspressoExecutorSalt.__type_cast(attrs)
            result = [{
                attr : type_(getattr(item, attr))
                for attr, type_ in cast.items()
                } for item in iterable]
        else:
            raise TypeError(
                'Attribute collection type error, use list or dict')
        return result

    ###########'public' user defined function #############
    def part_data(self, indices, attrs):
        """Retrieves attributes values from espressomd.system on the particles of given indices
        Cast the result to provided in attrs types (if attrs is dict).

        Args:
            indices (int, tuple, slice, list): indices to access the particles
            attrs (list, dict): attributes to access, you can provide type as a values of the dict to cast it before return

        Returns:
            list[dict]: list of attributes values of the respective particles
        """
        particles = self.__get_particles(indices)
        attributes = self.__get_and_cast_attributes(particles, attrs)

        if len(attributes) == 1: return attributes[0]
        return attributes

    def populate(self, n, **kwargs):
        """Populate the espressomd.System with n particles

        Args:
            n (int): Number of particles to add
        """
        [self.system.part.add(
            pos=self.system.box_l * np.random.random(3), **kwargs
            ) for _ in range(n)
        ]
        return True

    def add_particle(self, attrs_to_return, **kwargs):
        """Add a particle with **kwargs to the espressomd.System and returns its attributes

        Args:
            attrs_to_return (list, dict): [attribute_names] or {attribute_name : type_to_cast}

        Returns:
            list[dict]: list of attributes values of the added particle
        """
        def __missing_int(l) -> int:
            #makes new IDs predictable
            #[1,2,3,5,7] -> 4
            #[1,2,3,4,5,7] ->6
            for i in range(min(l), max(l)):
                if i not in l:
                    return i
        if 'id' not in kwargs:
            ids = list(self.system.part[:].id)
            new_id = __missing_int(ids)
            if new_id is None: pass
            else: kwargs.update({'id':new_id})
        if 'pos' not in kwargs:
            kwargs.update({'pos' : self.system.box_l * np.random.random(3)})
        added_particle_id = self.system.part.add(**kwargs).id
        return self.part_data(added_particle_id, attrs_to_return)

    def remove_particle(self, id, attrs_to_return):
        """Remove the particle with a given id and returns its attributes

        Args:
            id (int): particle's id
            attrs_to_return (list, dict): [attribute_names] or {attribute_name : type_to_cast}

        Returns:
            list[dict]: list of attributes values of the removed particle
        """
        removed_particle_attrs = self.part_data(id, attrs_to_return)
        self.system.part[id].remove()
        return removed_particle_attrs

    def potential_energy(self):
        """Access potential energy of the espressomd.System

        Returns:
            float: potential energy
        """
        return float(self.system.analysis.energy()['total'] - self.system.analysis.energy()['kinetic'])

    def sample_pressure_to_target(system, int_steps=1000, **kwargs):
        def get_data_callback(n):
                acc = []
                for i in range(n):
                    system.integrator.run(int_steps)
                    acc.append(float(system.analysis.pressure()['total']))
                return acc
        return sample_to_target_error(get_data_callback, **kwargs)

    def increment_volume(self, incr_vol, int_steps = 10000):
        system = self.system
        old_vol = system.box_l[0]**3
        new_vol = old_vol + incr_vol
        d_new = new_vol**(1/3)
        system.change_volume_and_rescale_particles(d_new)
        system.integrator.run(int_steps)
        print(f"Volume changed {old_vol} -> {new_vol}")
        return self.potential_energy()

    def change_volume(self, new_vol, int_steps = 10000):
        system = self.system
        d_new = new_vol**(1/3)
        system.change_volume_and_rescale_particles(d_new)
        system.integrator.run(int_steps)
        print(f"Volume changed to {new_vol}")
        return self.potential_energy()

    def enable_electrostatic(self, l_bjerrum=2, int_steps = 10000):
        from espressomd import electrostatics
        l_bjerrum = 2
        p3m = electrostatics.P3M(prefactor=l_bjerrum, accuracy=1e-3)
        self.system.actors.add(p3m)
        p3m_params = p3m.get_params()
        print(p3m_params)
        self.minimize_energy()
        return True

    def minimize_energy(self, dist=1, timeout = 60):
        system = self.system
        import time
        start_time = time.time()
        system.thermostat.suspend()
        system.integrator.set_steepest_descent(f_max=0, gamma=0.1, max_displacement=0.1)
        min_d = system.analysis.min_dist()
        print(f"Minimal distance: {min_d}")
        while (min_d < dist) or (min_d==np.inf):
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout:
                print('Timeout')
                break
            system.integrator.run(100)
            min_d = system.analysis.min_dist()
            print(f"Minimal distance: {min_d}")
        system.integrator.set_vv()
        system.thermostat.recover()
        self.system.integrator.run(10000)
        return min_d

class EspressoExecutorGel(EspressoExecutorSalt):
    def Re(self):
        from init_diamond_system import calc_Re, _get_pairs
        pairs = _get_pairs(self.system,0)
        Re = calc_Re(self.system, pairs)
        return Re

    def sample_Re(self, int_steps : int = 1000, n_samples : int = 100, return_only_mean = False):
        acc = []
        for i in range(n_samples):
            self.system.integrator.run(int_steps)
            acc.append(self.Re())
        if return_only_mean:
            return np.mean(acc), np.std(acc)
        else:
            return acc

    def sample_Re_to_target_error(
            self, target_error, initial_sample_size,
            tau = None, int_steps = 1000,
            timeout = 30, ci = 0.95):
        def get_data_callback(n):
            return self.sample_Re(int_steps=int_steps, n_samples = n)
        return sample_to_target_error(get_data_callback, target_error, initial_sample_size, tau, timeout, ci)

#%%
if __name__ == "__main__": ##for debugging
    system = espressomd.System(box_l = [20, 20, 20])
    system.time_step = 0.001
    system.cell_system.skin = 0.4
    system.thermostat.set_langevin(kT=1, gamma=1, seed=42)
    lj_sigma=1
    system.non_bonded_inter[0,0].lennard_jones.set_params(epsilon=1, sigma=lj_sigma, cutoff=lj_sigma*2**(1./6), shift='auto')
    executor = EspressoExecutorSalt(system)
    executor.populate(50, q=-1)
    executor.populate(50, q=+1)
#%%
    executor.minimize_energy(dist=1)
#%%
    executor.enable_electrostatic()
# %%
    executor.potential_energy()
# %%
