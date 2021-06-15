import os
import sys
import socket
import logging
import pickle
import threading
#from time import monotonic as time
from time import sleep

HEADER_LENGTH = 10

class ErrorRequest:
    def __init__(self, details) -> None:
        self.details = details

def send_data(data, server_socket):
    try:
        msg = pickle.dumps(data)
    except:
        msg = pickle.dumps('Non-pickable data')
    msg = bytes(f"{len(msg):<{HEADER_LENGTH}}", 'utf-8')+msg
    server_socket.send(msg)

def recv_data(server_socket):
    message_header = server_socket.recv(HEADER_LENGTH)
    if not len(message_header): return False
    message_length = int(message_header.decode('utf-8').strip())
    serialized_data = server_socket.recv(message_length)
    data = pickle.loads(serialized_data)
    return data

class BaseClient():

    request_queue=[]
    connected = False

    def __init__(self, IP, PORT, connect  = True, _io = None) -> None:
        self.IP = IP
        self.PORT = PORT
        self.logger = logging.getLogger('Client')
        if _io is None:
            self.recv = recv_data
            self.send = send_data
        else:
            self.recv = _io[0]
            self.send = _io[1]
        if connect:
            self.connect()

    def connect(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.connect((self.IP, self.PORT))
            self.logger.info('Connected to server')
            self.connected = True
        except Exception as e:
            self.logger.error(e)

    def get_requests(self):
        while self.connected:
            try:
                data = self.recv(self.server_socket)
                self.logger.debug('Request from server')
                if data == False:
                    self.logger.warning('Disconnected from server')
                    self.connected = False
                self.request_queue.append(data)
            except Exception as e:
                self.logger.error(e)
                self.request_queue.append(ErrorRequest('Request error'))

    def verify_request(self, request):
        return True

    def handle_request(self, request):
        self.logger.debug('Echo handle, 5s sleep')
        sleep(5)
        responce = request
        self.logger.debug('Echo done')
        return responce #echo

    def process_requests(self):
        while self.connected:
            if self.request_queue:
                request = self.request_queue.pop(0)
                self.logger.debug(f'Process request from queue\n request: {request}')
                if self.verify_request(request):
                    try:
                        responce = self.handle_request(request)
                    except Exception as e:
                        responce = ErrorRequest('Handle request error')
                else:
                    responce = ErrorRequest('Request is invalid')
                self.send(responce, self.server_socket)
                self.logger.debug(f'Done, sent to the host\n result: {responce}')

    def start(self):
        self.logger.debug(f'Threads are started...')
        threading.Thread(target=self.get_requests, daemon=True).start()
        threading.Thread(target=self.process_requests, daemon=True).start()
        

    def shutdown(self):
        self.logger.debug(f'Shuting down...')
        while self.request_queue:
            pass
        self.connected = False
        self.server_socket.close()
        self.logger.debug(f'Socket is closed')
