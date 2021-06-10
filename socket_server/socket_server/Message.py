class Message():
    def __init__(self, data, sender, receiver) -> None:
        self.data = data
        self.sender = sender
        self.receiver = receiver
        #self.wait_responce = wait_responce
