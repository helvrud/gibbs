import socket
import select
import pickle
import time

from .Message import Message

HEADER_LENGTH = 10

class SocketServer():
    #clients information
    sockets_list = []
    addr_list = []

    server_socket = None
    _active = True
    
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

    def _recv_object(self, client_socket):
        try:
            message_header = client_socket.recv(HEADER_LENGTH)

            #no data -> client closed a connection
            if not len(message_header):
                return False

            message_length = int(message_header.decode('utf-8').strip())

            serialized_data = client_socket.recv(message_length)
            data = pickle.loads(serialized_data)

            return data

        except:
            #client or server has been closed violently
            return False

    def _send_object(self, client_socket, data,):
        msg = pickle.dumps(data)
        msg = bytes(f"{len(msg):<{HEADER_LENGTH}}", 'utf-8')+msg
        client_socket.send(msg)

    def recv_message(self, client_addr):
        client_socket = self.sockets_list[self.addr_list.index(client_addr)]
        msg = self._recv_object(client_socket)
        if msg is False: return False
        if isinstance(msg, Message):
            if msg.receiver == 'host':
                self._income_msg_handle(msg)
            else:
                self._forwarding_msg_handle(msg)
            return True
        else:
            #raise TypeError("The data isn't wrapped into the Message class")
            print("HOST: The data isn't wrapped into the Message class")
            return None

    def send_message(self, data, client_addr):
        client_socket = self.sockets_list[self.addr_list.index(client_addr)]
        msg = Message(data = data, sender = 'host', receiver = client_addr)
        self._send_object(client_socket, msg)

    def _income_msg_handle(self, msg):
        print (f"HOST: [INCOME MESSAGE] from {msg.sender}")
        data = msg.data
        print (data)
        if data == "\STOP_SERVER":
            #the server 
            self._active = False
        elif data == "\ECHO":
            self.send_message('OK', msg.sender)

    def _forwarding_msg_handle(self, msg):
        client_addr = msg.receiver
        if client_addr in self.addr_list:
            client_socket = self.sockets_list[self.addr_list.index(client_addr)]
            print (f"HOST: [FORWARDING MESSAGE] from {msg.sender} to {client_addr}")
            self._send_object(client_socket, msg)
        else:
            print (f"HOST: Client is not found, forwarding failed")
            self.send_message('\FORWARDING_FAILED', msg.sender)

    def _new_conn_handle(self):
        client_socket, client_address = self.server_socket.accept()
        self.sockets_list.append(client_socket)
        self.addr_list.append(client_address)
        print(f'HOST: Accepted new connection from {client_address}')
        #sending to the connected client his address on the server
        self._send_object(client_socket, client_address)

    def _disconn_handle(self, client_socket):
        idx = self.sockets_list.index(client_socket)
        print(f'HOST: Connection with {self.addr_list[idx]} has been closed')
        del self.sockets_list[idx]
        del self.addr_list[idx]

    def _stop_server_routine(self, timeout = None):
        print ('HOST: The server will be stopped')
        #broadcast the message that server is stopped
        #for client_addr in self.addr_list:
        #    self.send_message('\STOP_SERVER', client_addr)
        #self._active = False
        if timeout is not None: time.sleep(timeout)
        self.server_socket.close()
        
    def listen(self):
        #find the socket where reading is happening
        read_sockets, _, exception_sockets = select.select(self.sockets_list, [], self.sockets_list)
        
        for notified_socket in read_sockets:
            #new connection
            if notified_socket == self.server_socket:
                self._new_conn_handle()
            
            #new message
            else:
                client_addr = self.addr_list[self.sockets_list.index(notified_socket)]
                if self.recv_message(client_addr) is False:
                    # client disconnected
                    self._disconn_handle(notified_socket)
                    continue

          
        for notified_socket in exception_sockets:
            # client disconnected violently
            self._disconn_handle(notified_socket)

    def loop(self):
        while self._active:
            #print('...')
            self.listen()
        else:
            self._stop_server_routine()

    def loop_thread(self):
        from threading import Thread
        p = Thread(target=self.loop)
        return p
