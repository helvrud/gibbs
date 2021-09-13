#%%
from typing import Callable
from socket_nodes import LocalScopeExecutor

##import all you might need later when requesting from server
import espressomd
import numpy as np

def get_tau(x, acf_n_lags : int = 200):
    from statsmodels.tsa.stattools import acf
    import numpy as np
    acf = acf(x, nlags = acf_n_lags)
    tau_int =1/2+max(np.cumsum(acf))    
    return tau_int

def correlated_data_mean_err(x, tau, ci = 0.95):
    import scipy.stats
    import numpy as np
    x_mean = np.mean(x)
    n_eff = np.size(x)/(2*tau)
    print(f"Effective sample size: {n_eff}")
    t_value=scipy.stats.t.ppf(1-(1-ci)/2, n_eff)
    print(f"t-value: {t_value}")
    err = np.std(x)/np.sqrt(n_eff) * t_value
    return x_mean, err
    
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
    @staticmethod
    def __type_cast(type_names_dict) -> dict:
        return {k : eval(f'{v}') for k, v in type_names_dict.items()}

    def __get_particles(self, indices):
        if isinstance(indices, int):
            particles = [self.system.part[indices]]
        elif isinstance(indices, slice):
            particles = self.system.part[indices]
        elif isinstance(indices, tuple):
            particles = self.system.part[slice(*indices)]
        elif isinstance(indices, list):
            particles = [self.system.part[id] for id in indices]
        else:
            raise TypeError('system.part[indices] indices type error')
        return particles
    
    def __get_and_cast_attributes(self, iterable, attrs):
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
        particles = self.__get_particles(indices)
        attributes = self.__get_and_cast_attributes(particles, attrs)
        
        if len(attributes) == 1: return attributes[0]
        return attributes

    def populate(self, n, **kwargs):
        [self.system.part.add(
            pos=self.system.box_l * np.random.random(3), **kwargs
            ) for _ in range(n)
        ]

    def add_particle(self, attrs_to_return, **kwargs):
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
        
    def remove_particle(self, id, attrs_to_member):
        removed_particle_attrs = self.part_data(id, attrs_to_member)
        self.system.part[id].remove()
        return removed_particle_attrs

    def potential_energy(self):
        return float(self.system.analysis.energy()['total'] - self.system.analysis.energy()['kinetic'])

    def pressure(self):
        return float(self.system.analysis.pressure()['total']) 

    def integrate_pressure(self, int_steps : int = 1000, n_samples : int = 100, return_only_mean = False):
        acc = []
        for i in range(n_samples):
            self.system.integrator.run(int_steps)
            acc.append(self.pressure())
        if return_only_mean:
            return np.mean(acc), np.std(acc)
        else:
            return acc

    def auto_integrate_pressure(self, target_error, initial_sample_size, ci = 0.95, tau = None, int_steps = 1000, timeout = 30):
        import time
        start_time = time.time()
        n_samples = initial_sample_size
        x = self.integrate_pressure(n_samples = n_samples, int_steps=int_steps)
        if tau is None: tau = get_tau(x)
        x_mean, x_err = correlated_data_mean_err(x, tau, ci)
        while x_err>target_error:
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout:
                print('Timeout')
                return x_mean, x_err, n_samples
            print(f'Error {x_err} is bigger than target')
            print('More data will be collected')
            x=x+self.integrate_pressure(n_samples = n_samples, int_steps=int_steps)
            if tau is None: tau = get_tau(x)
            x_mean, x_err = correlated_data_mean_err(x, tau, ci)
            n_samples = n_samples*2
        else:
            print(f'Mean: {x_mean}, err: {x_err}, eff_sample_size: {n_samples/(2*tau)}')
            return x_mean, x_err, n_samples/(2*tau)

    def increment_volume(self, incr_vol, int_steps = 10000):
        system = self.system
        old_vol = system.box_l[0]**3
        new_vol = old_vol + incr_vol
        d_new = new_vol**(1/3) 
        system.change_volume_and_rescale_particles(d_new)
        system.integrator.run(int_steps)
        print(f"Volume changed {old_vol} -> {new_vol}")
        return self.potential_energy()

class EspressoExecutorGel(EspressoExecutorSalt):
    def Re(self):
        from init_diamond_system import calc_Re, _get_pairs
        pairs = _get_pairs(self.system,0)
        Re = calc_Re(self.system, pairs)
        return Re

    def integrate_Re(self, int_steps : int = 1000, n_samples : int = 100, return_only_mean = False):
        acc = []
        for i in range(n_samples):
            self.system.integrator.run(int_steps)
            acc.append(self.Re())
        if return_only_mean:
            return np.mean(acc), np.std(acc)
        else:
            return acc

#%%
if __name__ == "__main__": ##for debugging
    system = espressomd.System(box_l = [10, 10, 10])
    system.time_step = 0.001
    system.cell_system.skin = 0.4
    system.thermostat.set_langevin(kT=1, gamma=1, seed=42)
    system.minimize_energy.init(f_max=50, gamma=30.0, max_steps=10000, max_displacement=0.001)
    lj_sigma=1
    system.non_bonded_inter[0,0].lennard_jones.set_params(epsilon=1, sigma=lj_sigma, cutoff=lj_sigma*2**(1./6), shift='auto')
    executor = EspressoExecutorSalt(system)
    executor.populate(50)
# %%
    executor.auto_integrate_pressure(0.00005, 1000)
# %%
