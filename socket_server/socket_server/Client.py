import socket
import pickle
import time

from .Message import Message

HEADER_LENGTH = 10
    
class Client():
    _connected = False
    last_message = None
    system = None
    def __init__(self, IP, PORT) -> None:
        self.IP = IP
        self.PORT = PORT

    def connect(self):
        if self._connected:
            pass #an error, do something
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.connect((self.IP, self.PORT))
        # Set connection to non-blocking state, so .recv() call won't block, just return some exception we'll handle
        #self.server_socket.setblocking(False)
        
        print("Connecting to a server...")
        #The server will send an address it assigned to a new client
        addr = self._recv_object()
        self.addr = addr
        print(f"Assigned addres: {self.addr}")
        self._connected = True

    def _send_object(self, data):
        try:
            msg = pickle.dumps(data)
        except:
            msg = pickle.dumps('The result can not be pickled')
        msg = bytes(f"{len(msg):<{HEADER_LENGTH}}", 'utf-8')+msg
        self.server_socket.send(msg)

    def _recv_object(self):
        message_header = self.server_socket.recv(HEADER_LENGTH)

        #client closed connection
        if not len(message_header):
            return False

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
            return True
        else:
            print("The data isn't wrapped into the Message class")
            return None

    def _income_client_message_handle(self, msg):
        print (f"[INCOME MESSAGE] from {msg.sender}")
        data = msg.data
        print (data)

    def _income_host_message_handle(self, msg):
        print (f"[INCOME MESSAGE] from {msg.sender}")
        data = msg.data
        print (data)
        if data == '\STOP_SERVER':
            print('Server is going to be stopped.')
            self._connected = False
        if isinstance(data, dict):
            if "eval" in data.keys(): #this one is very insecure, and should be deprecated
                if not isinstance(data['eval'], list): data['eval'] = [data['eval']]
                for item in data['eval']:
                    self.eval(item, 'host')

            if "exec" in data.keys():
                if not isinstance(data['exec'],list): data['exec'] = [data['exec']]
                for item in data['exec']:
                    self.exec(item, 'host')       

    def _disconn_routine(self, sys_exit = False):
        self.server_socket.close()
        if sys_exit:
            import sys
            sys.exit()

    def listen(self):
        #server closed a connection
        if self.recv_message() is False:
            print('Connection closed by the server')
            self._disconn_routine()

    def echo_test(self):
        self.send_message('\ECHO', 'host')
        self.recv_message()
        

    def loop(self):
        while self._connected:
            print(".")
            self.listen()
        else:
            self._disconn_routine()

    def loop_thread(self, flavor='threading'):
        if flavor=='threading':
            from threading import Thread
            p = Thread(target=self.loop)
            return p
        elif flavor=='multiprocessing':
            from multiprocessing import Process
            p = Process(target=self.loop)
            return p

    def eval(self, eval_str, result_receiver = None):
        print(f'eval({eval_str})')
        try:
            result = eval(eval_str)
        except Exception as e:
            result = e
        if result_receiver is not None:
            self.send_message(result, result_receiver)
        else:
            return result
    
    def exec(self, eval_str, result_receiver = None):
        print(f'exec({eval_str})')
        try:
            result = exec(eval_str)
        except Exception as e:
            result = e
        if result_receiver is not None:
            self.send_message(result, result_receiver)
        else:
            return result
        



import functools
import importlib
import numpy

class ObjectSocketInterface(Client):
    _object = None
    _commands = {}
    def __init__(self, IP, PORT) -> None:
        super().__init__(IP, PORT)

    def create_object(self, object_class, *args, **kwargs):
        print(f"Creating an instance {object_class}({args, kwargs})")
        self._object = object_class(*args, **kwargs)

    def _income_host_message_handle(self, msg):
        print (f"[INCOME MESSAGE] from {msg.sender}")
        if isinstance(msg.data, dict):
            _dict = msg.data
            if "eval" in _dict.keys(): #this one is very insecure, and should be deprecated
                if not isinstance(_dict['eval'],list): _dict['eval'] = [_dict['eval'] ]
                for item in _dict['eval']:
                    if '*.' in item:
                        eval_str = item.replace('*.','self._object.')
                        """ elif 'system.' == item[0:8]:
                            eval_str = 'self._object.'+item[0:8].replace('system.','self._object.')
                        elif 'system.' in item:
                            eval_str = item.replace('system.','self._object.') """
                    else:
                        eval_str = item
                    print(f"Trying eval({eval_str})")
                    try:
                        result = eval(eval_str)
                        print(f"eval({eval_str}) -> {result}")
                    except Exception as e:
                        print ('eval() failed')
                        result = e
                    self.send_message(result, msg.sender)
            if "cmd" in _dict.keys():
                if _dict['cmd'] == '\STOP':
                    print('Client will be closed')
                    self._connected = False

    def _rsetattr(self, attr, val):
        pre, _, post = attr.rpartition('.')
        return setattr(self._rgetattr(pre) if pre else self._object, post, val)

    def _rgetattr(self, attr, *args, **kwargs):
        def _getattr(obj, attr):
            return getattr(obj, attr, *args, **kwargs)
        return functools.reduce(_getattr, [self._object] + attr.split('.'))

