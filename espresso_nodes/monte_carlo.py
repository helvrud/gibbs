
class AbstractMonteCarlo:
    def __init__(self):
        pass
    
    def setup(self):
        pass

    def move(self):
        pass

    def reverse(self):
        pass

    def accept(self) -> bool:
        pass

    def on_accept(self):
        pass

    def on_reject(self):
        pass

    def step(self):
        pass