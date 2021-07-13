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
    logger = logging.getLogger
    def execute(self, expr):
        try:
            return eval(expr)
        except Exception as e:
            return e

class BaseExecutorNode(BaseNode):
    def __init__(self, IP, PORT, connect = True, ExecutorClass = EvalExecutor, executor_init_args = None) -> None:
        super().__init__(IP, PORT, connect=connect)
        if (executor_init_args is not None):
            self.Executor = ExecutorClass(*executor_init_args)
        else:
            self.Executor = ExecutorClass()
    def exec_request(self, request):
        return self.Executor.execute(request)
    def verify_request(self, request):
        return self.Executor.verify(request)



