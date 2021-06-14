import os
import sys
import socket
import logging
import pickle
import threading
from time import monotonic as time

HEADER_LENGTH = 10

class ErrorRequest:
    def __init__(self, details) -> None:
        self.details = details

def send_data(data, server_socket):
    msg = pickle.dumps(data)
    msg = bytes(f"{len(msg):<{HEADER_LENGTH}}", 'utf-8')+msg
    server_socket.send(msg)

def recv_data(server_socket):
    message_header = server_socket.recv(HEADER_LENGTH)
    if not len(message_header): return False
    message_length = int(message_header.decode('utf-8').strip())
    serialized_data = server_socket.recv(message_length)
    data = pickle.loads(serialized_data)
    return data

""" def send_data(data, server_socket):
    msg = pickle.dumps(data)
    msg = f"{len(msg):<{HEADER_LENGTH}}"+msg
    server_socket.send(bytes(msg,'utf-8'))

def recv_data(server_socket):
    message_header = server_socket.recv(HEADER_LENGTH)
    if not len(message_header): return False
    message_length = int(message_header.decode('utf-8').strip())
    data = server_socket.recv(message_length).decode('utf-8')
    return data """


class BaseClient():
    request_queue=[]
    responce_queue=[]
    connected = False
    client_address = None

    #request_queue_thread = None
    #responce_queue_thread = None

    
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
                self.logger.debug('Got request from server')
                if data == False:
                    self.logger.debug('Disconnected from server')
                    self.connected = False
                self.request_queue.append(data)
            except Exception as e:
                self.logger.error(e)
                self.request_queue.append(ErrorRequest('Get request error'))

    def verify_request(self, request):
        return True

    def handle_request(self, request):
        return request #echo

    def process_requests(self):
        while self.connected:
            if self.request_queue:
                request = self.request_queue.pop(0)
                if self.verify_request(request):
                    try:
                        responce = self.handle_request(request)
                    except Exception as e:
                        responce = ErrorRequest('Handle request error')
                else:
                    responce = ErrorRequest('Request is invalid')
                self.logger.debug('Request processed')
                self.send(responce, self.server_socket)
                #self.responce_queue.append(responce)
                #self.logger.debug(f'responce: {self.responce_queue}')
                

    #def send_responces(self):
    #    while self.connected:
    #        if self.responce_queue:
    #            self.logger.debug('Sending processed requests...')
    #            responce = self.responce_queue.pop(0)
    #            if self.connected:
    #                self.send(responce, self.server_socket)
    #                self.logger.debug('Responce sended')
    #            else:
    #                raise
    
    

    def start_threads(self):
        threading.Thread(target=self.get_requests, daemon=True).start()
        threading.Thread(target=self.process_requests, daemon=True).start()
        #threading.Thread(target=self.send_responces, daemon=True).start()
        

    def shutdown(self):
        while self.responce_queue or self.request_queue:
            pass
        self.server_socket.close()
