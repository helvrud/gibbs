import argparse
from logging import log
from socket_nodes import BaseExecutor
from socket_nodes import Node

class EvalExecutorClass(BaseExecutor):
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

    parser.add_argument('--log_name',
                        metavar='log_name',
                        help = 'name of log file',
                        type = str,
                        required=False)
    args = parser.parse_args()

    if args.log_name:
        import logging
        logging.basicConfig(filename=args.log_name,
                            level = logging.DEBUG)
        logging.info(__name__ + ' started')

    #instantiates the node
    node = Node(args.IP, args.PORT, EvalExecutorClass)
    #node's forever loop
    node.run()

    #The node had closed
    print("Closed")