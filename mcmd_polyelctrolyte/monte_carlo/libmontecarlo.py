from typing import Tuple
class ReversalData(dict):
    pass

class StateData(dict):
    pass

class AcceptCriterion(dict):
    pass

class AbstractMonteCarlo:
    current_state : StateData
    def __init__(self):
        pass
    
    def setup(self) -> StateData:
        pass

    def move(self) -> Tuple[ReversalData, AcceptCriterion]:
        pass

    def reverse(self, reverse_data : ReversalData):
        pass

    def accept(self, criterion: AcceptCriterion) -> bool:
        import random
        import math
        dE = criterion['dE']
        dS = criterion['dS']
        beta = criterion['beta']
        dF = dE-dS
        if dF<0:
            return True
        else:
            prob = math.exp(-beta*dF)
            return (prob > random.random())

    def on_accept(self):
        pass

    def on_reject(self):
        pass

    def update_state(self, reversal : ReversalData):
        pass

    def step(self):
        reversal, accept_criterion = self.move()
        if self.accept(accept_criterion):
            self.update_state(reversal)
            self.on_accept()
        else:
            self.reverse(reversal)
            self.on_reject()
        return self.current_state




