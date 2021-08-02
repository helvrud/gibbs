from sys import executable
from socket_nodes import LocalScopeExecutor, Node
##import all you might need later when requesting from server
import espressomd
import re
import numpy as np
import random
import math

import logging
logging.basicConfig(level=logging.DEBUG)
class EspressoExecutor(LocalScopeExecutor):
    ###########overridden base class functions #############
    def __init__(self, espresso_system_instance) -> None:
        super().__init__()
        if 'system' not in globals():
            raise(RuntimeError('espressomd.System is not initialized'))
        else:
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
            cast = EspressoExecutor.__type_cast(attrs)
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
        [system.part.add(
            pos=system.box_l * np.random.random(3), **kwargs
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
            ids = list(system.part[:].id)
            new_id = __missing_int(ids)
            if new_id is None: pass
            else: kwargs.update({'id':new_id})
        if 'pos' not in kwargs:
            kwargs.update({'pos' : system.box_l * np.random.random(3)})
        added_particle_id = system.part.add(**kwargs).id
        return self.part_data(added_particle_id, attrs_to_return)
        
    def remove_particle(self, id, attrs_to_member):
        removed_particle_attrs = self.part_data(id, attrs_to_member)
        system.part[id].remove()
        return removed_particle_attrs

    def potential_energy(self):
        return float(system.analysis.energy()['total'] - system.analysis.energy()['kinetic'])

    def run_md(self, steps, sample_steps=100):
        i=0
        energy_acc=[]
        while i<steps:
            system.integrator.run(sample_steps)
            i+=sample_steps
            energy_acc.append(self.potential_energy())
        return np.array(energy_acc)

#an entry point to run the node in subprocesses
if __name__=="__main__":
    import argparse
    import sys
    parser = argparse.ArgumentParser(description='IP')
    parser.add_argument('IP',
                        metavar='IP',
                        type=str,
                        help='IP')
    parser.add_argument('PORT',
                        metavar='PORT',
                        type=int,
                        help='PORT')
    parser.add_argument('-l', 
                        metavar='l',
                        type = float,
                        help = 'box_size',
                        required=True)
    parser.add_argument('--salt', 
                        help = 'salt reservoir',
                        action='store_true',
                        required=False)
    parser.add_argument('--gel', 
                        help = 'add gel to the system',
                        action='store_true',
                        required=False)
    parser.add_argument('-MPC', 
                        metavar='MPC',
                        type = int,
                        help = 'particles between nodes',
                        required='--gel' in sys.argv)
    parser.add_argument('-bond_length', 
                        metavar='bond_length',
                        type = float,
                        help = 'bond length',
                        required='--gel' in sys.argv)
    parser.add_argument('-alpha', 
                        metavar='alpha',
                        type = float,
                        help = 'charged monomer ratio',
                        required='--gel' in sys.argv)
    args = parser.parse_args()
    
    if '--salt' in sys.argv:
        from init_reservoir_system import init_reservoir_system
        print('Initializing salt reservoir')
        system = init_reservoir_system(args.l)
    elif '--gel' in sys.argv:
        from init_diamond_system import init_diamond_system
        print('Initializing reservoir with a gel')
        system = init_diamond_system(args.MPC, args.bond_length, args.alpha, target_l=args.l)

    node = Node(args.IP, args.PORT, EspressoExecutor, system)
    node.run()