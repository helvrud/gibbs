import socket
import logging


class BaseClient():
    HEADER_LENGTH = 10
    def __init__(self, IP, PORT, RequestHandlerClass) -> None:
        self.IP = IP
        self.PORT = PORT
        self.logger = logging.getLogger('Client')
        self.RequestHandlerClass = RequestHandlerClass

    def connect(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.connect((self.IP, self.PORT))
            self.logger.info('Connected to server')
        except Exception as e:
            self.logger.error(e)

    def get_request():
        pass

    def verify_request():
        pass

    def process_request():
        pass

    def handle_timeout():
        pass

    def handle_request():
        passgit 

    def shutdown():
        pass

    def in_loop_actions():
        pass




