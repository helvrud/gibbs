from Node import BaseNode
import logging

class BaseExecutor:
    def __init__(self) -> None:
        pass
    def verify(self, expr):
        return True
    def execute(self, expr):
        pass

class EvalExecutor(BaseExecutor):
    def execute(self, expr):
        try:
            return eval(expr)
        except Exception as e:
            return e

class BaseExecutorNode(BaseNode):
    def __init__(self, IP, PORT, ExecutorClass = EvalExecutor, executor_init_args = None) -> None:
        super().__init__(IP, PORT)
        if (executor_init_args is not None):
            self.Executor = ExecutorClass(*executor_init_args)
        else:
            self.Executor = ExecutorClass()
    async def execute(self, request):
        return self.Executor.execute(request)
    async def verify(self, request):
        return self.Executor.verify(request)

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
    node = BaseExecutorNode(args.IP, args.PORT)
    node.run()



