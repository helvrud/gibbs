from socket_nodes import Executor, Node
##import all you might need later when requesting from server
import espressomd
import re
import numpy as np
import random
import math
from collections import Collection


class EspressoExecutor(Executor):
    def __init__(self, espresso_system_instance) -> None:
        super().__init__()
        self.system = espresso_system_instance
    def preprocess_string(self, str_) -> str:
        if str_[0]=='/':
            #user defined function (aliases or shortcuts) has to be called
            result_str = 'self.'+str_[1:]
        else:
            #do not need to write self.system.*, system.* is now valid
            PATTERN = re.compile(r'(?<![a-zA-Z0-9._])system(?![a-zA-Z0-9_])')
            result_str= PATTERN.sub(r'self.system', str_)
        return result_str

    def execute(self, expr_):
        if isinstance(expr_, list):
            return self.execute_multi_line(expr_)
        else:
            return self.execute_one_line(expr_)

    def execute_one_line(self, expr_ : str):
        expr = self.preprocess_string(expr_)
        try:
            return eval(expr)
        except Exception as e:
            return e

    def execute_multi_line(self, expr_ : list):
        return [self.execute_one_line(expr_line) for expr_line in expr_]
    
    ########### additional user defined function #############
    ######### for frequent requests, aliases or shorthands####
    ######### to use just request 'self.function_name(args)'##
    ######### or start command with / ########################
    @staticmethod
    def __type_cast(type_names_dict) -> dict:
        return {k : eval(f'{v}') for k, v in type_names_dict.items()}

    def part_data(self, id, attrs):
        if not isinstance(id,slice): 
            try:
                id = slice(*id)
            except:
                try:
                    id = slice(id, id+1)
                except:
                    id = slice(id)
        particles = self.system.part[id]

        if isinstance(attrs, list):
            return {attr : getattr(particles, attr) 
                    for attr in attrs}
        
        elif isinstance(attrs, dict):
            cast = EspressoExecutor.__type_cast(attrs)
            result = [{
                attr : type_(getattr(part, attr))
                for attr, type_ in cast.items()
                } for part in particles]
        
        if len(result) == 1: return result[0]
        
        return result

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
        part = self.system.part.add(**kwargs)
        if isinstance(attrs_to_return, list):
            return {attr : getattr(part, attr) for attr in attrs_to_return} 
        elif isinstance(attrs_to_return, dict):
            cast = EspressoExecutor.__type_cast(attrs_to_return)
            return {
                attr : type_(getattr(part, attr)) 
                for attr,type_ in cast.items()
                }

    def remove_particle(self, id, attrs_to_remember):
        if isinstance(attrs_to_remember, list):
            attrs =  {
                attr :
                getattr(self.system.part[id], attr) for attr in attrs_to_remember
                }
        elif isinstance(attrs_to_remember, dict):
            cast = EspressoExecutor.__type_cast(attrs_to_remember)
            attrs =  {
                attr : type_(getattr(self.system.part[id], attr)) 
                for attr, type_ in cast.items()
                }
        self.system.part[id].remove()
        return attrs

    def potential_energy(self):
        return float(self.system.analysis.energy()['total'] - self.system.analysis.energy()['kinetic'])

    def run_md(self, steps, sample_steps=100):
        i=0
        energy_acc=[]
        while i<steps:
            self.system.integrator.run(sample_steps)
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
        print('Initializing salt reservoir')
        system = espressomd.System(box_l = [args.l]*3)
    elif '--gel' in sys.argv:
        from init_diamond_system import init_diamond_system
        print('Initializing reservoir with a gel')
        system = init_diamond_system(args.MPC, args.bond_length, args.alpha) #!!

    node = Node(args.IP, args.PORT, EspressoExecutor, system)
    node.run()