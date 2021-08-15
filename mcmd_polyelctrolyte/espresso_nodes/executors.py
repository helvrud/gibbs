from typing import Callable
from socket_nodes import LocalScopeExecutor


##import all you might need later when requesting from server
import espressomd
import re
import numpy as np
import random
import math


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

    def _integrate_observable_callback(self):
        return self.pressure()

    def integrate(self, sample_size : int = 100, int_steps : int = 1000):
        acc = []
        for i in range(sample_size):
            self.system.integrator.run(int_steps)
            acc.append(self._integrate_observable_callback())
        return np.mean(acc), np.std(acc)


class EspressoExecutorGel(EspressoExecutorSalt):
    def Re(self):
        from init_diamond_system import calc_Re, _get_pairs
        pairs = _get_pairs(self.system,0)
        Re = calc_Re(self.system, pairs)
        return Re

    def _integrate_observable_callback(self):
        return self.Re()
