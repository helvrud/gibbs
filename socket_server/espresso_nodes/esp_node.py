from socket_nodes import Executor, Node
##import all you might need later when requesting from server
import espressomd
import re
import numpy as np
import random
import math



class EspressoExecutor(Executor):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__()
        self.system = espressomd.System(*args, **kwargs)
    
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
    def part_data(self, id, attrs):
        return [getattr(self.system.part[id], attr) for attr in attrs]

    def populate(self, n, **kwargs):
        [self.system.part.add(
            pos=self.system.box_l * np.random.random(3), **kwargs
            ) for _ in range(n)
        ]

    def add_particle(self, attrs_to_return : list, **kwargs):
        def __missing_int(l) -> int:
            #makes new IDs predictable
            #[1,2,3,5,7] -> 4
            #[1,2,3,4,5,7] ->6
            for i in range(min(l), max(l)):
                if i not in l:
                    return i
        if 'id' not in kwargs:
            print('no_id')
            ids = list(self.system.part[:].id)
            new_id = __missing_int(ids)
            if new_id is None: pass
            else: kwargs.update({'id':new_id})
        if 'pos' not in kwargs:
            kwargs.update({'pos' : self.system.box_l * np.random.random(3)})
        print(kwargs)
        part = self.system.part.add(**kwargs)
        return [getattr(part, attr) for attr in attrs_to_return]

    def remove_particle(self, id, attrs_to_remember : list):
        attrs =  [
            getattr(self.system.part[id], attr) for attr in attrs_to_remember
            ]
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
    parser = argparse.ArgumentParser(description='IP')
    parser.add_argument('IP',
                        metavar='IP',
                        type=str,
                        help='IP')
    parser.add_argument('PORT',
                        metavar='PORT',
                        type=int,
                        help='PORT')

    parser.add_argument('L',
                        metavar='L',
                        type=float,
                        help='system box length')

    args = parser.parse_args()
    node = Node(args.IP, args.PORT, EspressoExecutor, box_l = [args.L]*3)
    node.run()