import numpy as np
import argparse
from time import sleep
from socket_nodes import Executor
from socket_nodes import Node


class EvalExecutorClass(Executor):
    #example of an ExecutorClass implementation, tries to eval(expression)
    #returns the result if success or an error
    #only execute method has been overridden
    def execute(self, expr):
        try:
            return eval(expr)
        except Exception as e:
            return e


#an entry point to run the node in subprocesses
if __name__=="__main__":
    #describes which arguments we can pass to the script
    parser = argparse.ArgumentParser(description='args')
    parser.add_argument('IP',
                        metavar='IP',
                        type=str,
                        help='IP')
    parser.add_argument('PORT',
                        metavar='PORT',
                        type=int,
                        help='PORT')
    args = parser.parse_args()

    #instantiates the node
    node = Node(args.IP, args.PORT, EvalExecutorClass)
    #node's forever loop
    node.run()