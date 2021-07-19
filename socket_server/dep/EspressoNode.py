from ExecutorNode import *
import numpy as np
import espressomd
import re

class EspressoExecutor(BaseExecutor):
    def __init__(self) -> None:
        super().__init__()
        self.system = espressomd.System(box_l=[10,10,10])
    
    def preprocess_string(self, str_) -> str:
        #do not need to write self.system.*, system.* is now valid
        PATTERN = re.compile(r'(?<![a-zA-Z0-9._])system(?![a-zA-Z0-9_])')
        result_str= PATTERN.sub(r'self.system', str_)
        return result_str

    def execute(self, expr_):
        expr = self.preprocess_string(expr_)
        try:
            return eval(expr)
        except Exception as e:
            return e

class EspressoNode(BaseExecutorNode):
    pass

if __name__=="__main__":
    from time import sleep
    import numpy as np
    import argparse
    parser = argparse.ArgumentParser(description='IP')
    parser.add_argument('IP',
                        metavar='IP',
                        type=str,
                        help='IP')
    parser.add_argument('PORT',
                        metavar='PORT',
                        type=str,
                        help='PORT')

    args = parser.parse_args()
    node = EspressoNode(args.IP, args.PORT, ExecutorClass=EspressoExecutor)
    node.run()