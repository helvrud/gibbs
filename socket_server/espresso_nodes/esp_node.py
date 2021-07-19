from socket_nodes import Executor, Node
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