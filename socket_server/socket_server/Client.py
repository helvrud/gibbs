from os import error
import socket
import pickle
#import time
#import numpy

from .Message import Message

HEADER_LENGTH = 10

class ClientBase():
    _connected = False
    logs = []
    
    def __init__(self, IP, PORT) -> None:
        self.IP = IP
        self.PORT = PORT

    def connect(self):
        if self._connected:
            self.logs.append('Connection failed.')
            return None
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.connect((self.IP, self.PORT))
        # Set connection to non-blocking state, so .recv() call won't block, just return some exception we'll handle
        #self.server_socket.setblocking(False)
        
        self.logs.append("Connected to a server.")
        #The server will send an address it assigned to a new client
        addr = self._recv_object()
        self.addr = addr
        self.logs.append(f"Assigned addres: {self.addr}")
        self._connected = True

    def _send_object(self, data):
        msg = pickle.dumps(data)
        msg = bytes(f"{len(msg):<{HEADER_LENGTH}}", 'utf-8')+msg
        self.server_socket.send(msg)

    def _recv_object(self):
        message_header = self.server_socket.recv(HEADER_LENGTH)
        #client closed connection
        if not len(message_header): return False
        
        message_length = int(message_header.decode('utf-8').strip())
        serialized_data = self.server_socket.recv(message_length)
        data = pickle.loads(serialized_data)
        return data

    def send_message(self, data, receiver):
        msg = Message(data, sender = self.addr, receiver = receiver)
        self._send_object(msg)

    def recv_message(self):
        msg = self._recv_object()
        if msg is False: return False
        if isinstance(msg, Message):
            self.last_message = msg
            if msg.sender == 'host':
                self._income_host_message_handle(msg)
            else:
                self._income_client_message_handle(msg)
            return msg
        else:
            self.logs.append("The data isn't wrapped into the Message class")
            raise TypeError("The data isn't wrapped into the Message class")

    def _income_client_message_handle(self, msg):
        self.logs.append(f"[INCOME MESSAGE] from {msg.sender}")
        data = msg.data
        self.logs.append(data)

    def _income_host_message_handle(self, msg):
        self.logs.append(f"[INCOME MESSAGE] from {msg.sender}")
        data = msg.data
        self.logs.append(data)
        if isinstance(data,str): 
            if(data == '\STOP_SERVER'):
                self.logs.append('Server is going to be stopped.')
                self._connected = False
            if(data == '\ECHO'):
                self.send_message('\ECHO_OK', 'host')

    def echo_host(self):
        self.send_message('\ECHO', 'host')
        msg = self.recv_message()
        if (msg.sender == 'host') & (msg.data == '\ECHO_OK'):
            return True
        else:
            return False
   
    def _disconn_routine(self, sys_exit = True):
        self.server_socket.close()
        if sys_exit:
            import sys
            sys.exit()

    def listen(self):
        #server closed a connection
        if self.recv_message() is False:
            self.logs.append('Connection closed by the server')
            self._connected = False
            self._disconn_routine()

    def flush_log(self):
        while self.logs:
            print(self.logs.pop(0))

    def loop(self):
        while self._connected:
            self.listen()
            self.flush_log()
        else:
            self._disconn_routine()





class Client(ClientBase):
    _connected = False
    last_message = None

    def _income_host_message_handle(self, msg):
        super()._income_host_message_handle(msg)
        data = msg.data
        if isinstance(data, dict):
            if "eval" in data.keys(): #this one is very insecure, and should be deprecated
                if not isinstance(data['eval'], list): data['eval'] = [data['eval']]
                for item in data['eval']:
                    try:
                        result = self.eval(item)
                    except:
                        result = 'EVAL_FAILED'
                    try:
                        self.send_message(result, 'host')
                    except:
                        self.send_message('Result can not be serialized', 'host')

    def _income_client_message_handle(self, msg):
        super()._income_client_message_handle(msg)
        data = msg.data
        if "eval" in data.keys(): #this one is very insecure, and should be deprecated
                if not isinstance(data['eval'], list): data['eval'] = [data['eval']]
                for item in data['eval']:
                    try:
                        result = self.eval(item)
                    except:
                        result = 'EVAL_FAILED'
                    try:
                        self.send_message(result, msg.receiver)
                    except:
                        self.send_message('Result can not be serialized', msg.receiver)

    def loop_thread(self, flavor='threading'):
        if flavor=='threading':
            from threading import Thread
            p = Thread(target=self.loop)
            return p
        elif flavor=='multiprocessing':
            from multiprocessing import Process
            p = Process(target=self.loop)
            return p

    def eval(self, eval_str):
        result = eval(eval_str)
        return result
