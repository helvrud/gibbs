import socket
import select
import sys
import errno
import pickle
from collections import namedtuple
import uuid
import time

HEADER_LENGTH = 10

class Message():
    pass

class SocketServer():
    sockets_list = []
    addr_list = []
    server_socket = None
    active = True
    
    def __init__(self, IP, PORT) -> None:
        self.IP = IP
        self.PORT = PORT
    
    def start(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        #reuse blocked sockets
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        server_socket.bind((self.IP, self.PORT))
        print(f'Listening to {self.IP} ...')
        server_socket.listen()

        self.server_socket = server_socket
        self.sockets_list = [self.server_socket]
        self.addr_list = ['host']

    def recv_object(self, client_socket):
        try:
            message_header = client_socket.recv(HEADER_LENGTH)

            # If we received no data, client gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
            if not len(message_header):
                return False

            message_length = int(message_header.decode('utf-8').strip())

            serialized_data = client_socket.recv(message_length)
            data = pickle.loads(serialized_data)

            return data

        except:

            # If we are here, client closed connection violently, for example by pressing ctrl+c on his script
            # or just lost his connection
            # socket.close() also invokes socket.shutdown(socket.SHUT_RDWR) what sends information about closing the socket (shutdown read/write)
            # and that's also a cause when we receive an empty message
            return False

    def send_object(self, client_socket, data,):
        msg = pickle.dumps(data)
        msg = bytes(f"{len(msg):<{HEADER_LENGTH}}", 'utf-8')+msg
        client_socket.send(msg)

    def handle_new_connection(self):
        client_socket, client_address = self.server_socket.accept()
        self.sockets_list.append(client_socket)
        self.addr_list.append(client_address)
        print('Accepted new connection from {}:{}'.format(*client_address))
        self.send_object(client_socket, client_address)

    def handle_disconnection(self, client_socket):
        idx = self.sockets_list.index(client_socket)
        print(f'Connection with {self.addr_list[idx]} has been closed')
        del self.sockets_list[idx]
        del self.addr_list[idx]
        
    def listen_messages_or_connections(self):
        read_sockets, _, exception_sockets = select.select(self.sockets_list, [], self.sockets_list)
        
        for notified_socket in read_sockets:
            #new connection
            if notified_socket == self.server_socket:
                self.handle_new_connection()
            #new message
            else:

                # Receive message
                message = self.recv_object(notified_socket)
                try:
                    idx = self.sockets_list.index(notified_socket)
                    message.sender = self.addr_list[idx]
                except:
                    print("Can not add .sender attribute")
                    pass
                self.message_handle(message)

                # client disconnected
                if message is False:
                    self.handle_disconnection(notified_socket)
                    continue

                
        for notified_socket in exception_sockets:
            self.sockets_list.remove(notified_socket)

    def message_handle(self, message):
        if hasattr(message,"receiver"):
            if message.receiver=='host':
                print(f"[SERVER INCOME] from {message.sender}")
                self.income_server_message_handle(message.data)
            else:
                print(f"[SERVER FORWARDING] from {message.sender} to {message.receiver}")
                try:
                    idx = self.addr_list.index(message.receiver)
                    receiver_socket = self.sockets_list[idx]
                    self.send_object(receiver_socket, message)
                except:
                    print('Error forwarding')

    def income_server_message_handle(self, request):
        if request == 'STOP_SERVER':
            self.active = False

    def server_loop(self):
        while self.active:
            self.listen_messages_or_connections()
        else:
            self.server_socket.close()

class Client():
    connected = False    
    def __init__(self, IP, PORT) -> None:
        self.IP = IP
        self.PORT = PORT

    def connect(self):
        if self.connected:
            pass
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.connect((self.IP, self.PORT))
        # Set connection to non-blocking state, so .recv() call won't block, just return some exception we'll handle
        #self.server_socket.setblocking(False)
        print("Connected")
        addr = self.recv_object()
        self.addr = addr
        print(f"Assigned addres: {self.addr}")
        self.connected = True

    def send_object(self, data):
        msg = pickle.dumps(data)
        msg = bytes(f"{len(msg):<{HEADER_LENGTH}}", 'utf-8')+msg
        self.server_socket.send(msg)

    def recv_object(self):
        # Receive our "header" containing message length, it's size is defined and constant
        message_header = self.server_socket.recv(HEADER_LENGTH)

        # If we received no data, client gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
        if not len(message_header):
            return False

        message_length = int(message_header.decode('utf-8').strip())

        # Return an object of message header and message data
        serialized_data = self.server_socket.recv(message_length)
        data = pickle.loads(serialized_data)

        return data

    def send_addr(self):
        self.send_object(self.addr)

    def disconnect(self):
        self.server_socket.close()
        self.connected = False

    def listen_messages(self):
        msg = self.recv_object()
        # If we received no data, server gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
        if msg is False:
            print('Connection closed by the server')
            self.disconnect()
        else:
            self.message_handle(msg)

    def message_handle(self, message):
        if hasattr(message,"sender"):
            print(f"[INCOME MESSAGE] from: {message.sender}")
            print(message.data)

    def loop(self):
        while True:
            print(".")
            self.listen_messages()
            
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

