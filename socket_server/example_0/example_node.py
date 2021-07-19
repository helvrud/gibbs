import numpy as np
import argparse
from time import sleep
from socket_nodes import Executor
from socket_nodes import Node
class EvalExecutorClass(Executor):
    #example of an ExecutorClass implementation, tries to eval(expression)
    #returns the result if success or an error
    def execute(self, expr):
        try:
            return eval(expr)
        except Exception as e:
            return e

if __name__=="__main__":
    parser = argparse.ArgumentParser(description='IP')
    parser.add_argument('IP',
                        metavar='IP',
                        type=str,
                        help='IP')
    parser.add_argument('PORT',
                        metavar='PORT',
                        type=int,
                        help='PORT')

    args = parser.parse_args()
    node = Node(args.IP, args.PORT, EvalExecutorClass)
    node.event_loop()