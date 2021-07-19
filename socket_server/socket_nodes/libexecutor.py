class BaseExecutorClass:
    """
    Class to be inherited to construct user ExecutorNode
    """    
    def __init__(self) -> None:
        pass
    def verify(self, expr):
        return True
    def execute(self, expr):
        pass

