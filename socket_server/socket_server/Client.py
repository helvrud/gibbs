import socket
import pickle
import time

from .Message import Message

HEADER_LENGTH = 10

HEADER_LENGTH = 10

class Client():
    _connected = False
    last_message = None   
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
        msg = pickle.dumps(data)
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

    def _disconn_routine(self):
        self.server_socket.close()

    def listen(self):
        #server closed a connection
        if self.recv_message() is False:
            print('Connection closed by the server')
            self._disconn_routine()

    def echo_test(self):
        self.send_message('\ECHO', 'host')
        self.recv_message()
        

    def loop(self):
        while True:
            print(".")
            self.listen()
            
            """ except IOError as e:
                # This is normal on non blocking connections - when there are no incoming data error is going to be raised
                # Some operating systems will indicate that using AGAIN, and some using WOULDBLOCK error code
                # We are going to check for both - if one of them - that's expected, means no incoming data, continue as normal
                # If we got different error code - something happened
                if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                    print('Reading error: {}'.format(str(e)))
                    sys.exit()

                # We just did not receive anything
                continue

            except Exception as e:
                # Any other exception - something happened, exit
                print('Reading error: '.format(str(e)))
                sys.exit() """