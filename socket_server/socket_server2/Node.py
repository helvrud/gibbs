import os
import sys
import socket
import logging
import pickle
import threading
#from time import monotonic as time
from time import sleep

#logging.basicConfig(stream=open('log', 'w'), level=logging.DEBUG)
logger = logging.getLogger('Node')


class ErrorRequest:
    def __init__(self, details) -> None:
        self.details = details


class BaseNode():
    request_queue = []
    connected : bool = False

    def __init__(self, IP, PORT, connect  = True) -> None:
        self.IP = IP
        self.PORT = PORT
        if connect:
            self.connect()

    def connect(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.connect((self.IP, self.PORT))
            self.connected = True
            logger.info('Node connected to server')
        except Exception as e:
            logger.error(e)


    def listen(self):
        while self.connected:
            logger.debug('Listening...')
            try:
                data = self.recv_raw()
                if data == False:
                    self.handle_disconnection()
                else:
                    self.handle_request(data)
            except Exception as e:
                logger.error(e)
            except:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                logger.error(exc_type, exc_value, exc_traceback)


    def handle_request(self, request):
        self.request_queue.append(request)


    def handle_disconnection(self):
        logger.warning('Disconnected from server')
        self.connected = False


    def verify_request(self, request):
        return True


    def exec_request(self, request):
        logger.debug('eval test')
        #sleep(5)
        try:
            responce = eval(request)
        except Exception as e:
            responce = e
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logger.debug(exc_type, exc_value, exc_traceback)
        return responce


    def send_responce(self, responce):
        try:
            self.send_raw(responce)
        except Exception as e:
            logger.debug(e)
            self.connected = False
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logger.debug(exc_type, exc_value, exc_traceback)
            self.connected = False


    def process_request_queue(self):
        while self.connected:
            try:
                request = self.request_queue.pop(0)
                logger.debug(f'Process request from queue\n request: {request}')
                self.process_request(request)
            except IndexError:
                 pass

                
    def process_request(self, request):
        if self.verify_request(request):
            responce = self.exec_request(request)
        else:
            responce = ErrorRequest('Request is invalid')
        self.send_responce(responce)
        logger.debug(f'Done, sent to the host\n result: {responce}')


    def start(self):
        logger.debug(f'Threads are started...')
        threading.Thread(target=self.listen, daemon=True).start()
        threading.Thread(target=self.process_request_queue, daemon=True).start()
        

    def shutdown(self):
        logger.debug(f'Shuting down...')
        while self.request_queue:
            pass
        self.connected = False
        self.server_socket.close()
        logger.debug(f'Socket is closed')


    def recv_raw(self):
        HEADER_LENGTH = 10
        try:
            message_header = self.server_socket.recv(HEADER_LENGTH)
            #no data -> client closed a connection
            if not len(message_header):
                return False
            message_length = int(message_header.decode('utf-8').strip())
            serialized_data = self.server_socket.recv(message_length)
            data = pickle.loads(serialized_data)
            return data
        except Exception as e:
            logger.error(e)
            return False


    def send_raw(self, data):
        HEADER_LENGTH = 10
        msg = pickle.dumps(data)
        msg = bytes(f"{len(msg):<{HEADER_LENGTH}}", 'utf-8')+msg
        self.server_socket.send(msg)
