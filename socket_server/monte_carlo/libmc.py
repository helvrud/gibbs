class Monte_Carlo:
    def __init__(self) -> None:
        pass

    def move(self):
        pass

    def reverse(self, reversal_data):
        pass

    def accept(self, energy_change):
        pass

    def step(self):
        reversal_data, energy_change = self.move()
        if self.accept():
            pass
        else:
            self.reverse(reversal_data)
