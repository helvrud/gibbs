import socket
import threading
import logging
import pickle
import select

HEADER_LENGTH = 10

def recv_data(client_socket):
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
        return False

def send_data(client_socket, data):
    msg = pickle.dumps(data)
    msg = bytes(f"{len(msg):<{HEADER_LENGTH}}", 'utf-8')+msg
    client_socket.send(msg)

""" def recv_data(client_socket):
    #try:
    message_header = client_socket.recv(HEADER_LENGTH)
    #no data -> client closed a connection
    if not len(message_header): return False
    message_length = int(message_header.decode('utf-8').strip())
    data = client_socket.recv(message_length).decode('utf-8')
    return data
    #except:
    #    return False

def send_data(client_socket, data):
    msg = pickle.dumps(data)
    msg = f"{len(msg):<{HEADER_LENGTH}}"+msg
    client_socket.send(bytes(msg,'utf-8')) """


class RequestClass():
    responce = None
    def __init__(self, request):
        self.request = request
        self.DONE = False
        self.thread = threading.Thread(target = self.wait_responce)
    def wait_responce(self):
        while not self.DONE:
            pass
        else:
            return self.responce


class _ConnectedClient():
    works = 0
    def __init__(self, client_addr, client_socket, server_addr) -> None:
        self.addr = client_addr
        self.socket = client_socket
        self.server_addr

class BaseSocketServer():



    
    
    
    active = False
    non_blocking_request_responce = {}
    
    sockets_list = []
    addr_list = []
    
    server_socket = None

    def __init__(self, IP, PORT, _io = None) -> None:
        self.IP = IP
        self.PORT = PORT
        self.logger = logging.getLogger('Server')
        if _io is None:
            self.recv = recv_data
            self.send = send_data
        else:
            self.recv = _io[0]
            self.send = _io[1]

    def setup(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #server_socket.settimeout(30.0)
        server_socket.setblocking(0)

        server_socket.bind((self.IP, self.PORT))
        self.logger.debug(f'HOST: Listening to {self.IP} ...')
        server_socket.listen()

        self.active = True
        self.server_socket = server_socket
        self.sockets_list = [self.server_socket]
        self.addr_list = ['host']

    def handle_connection(self):
        client_socket, client_address = self.server_socket.accept()
        self.sockets_list.append(client_socket)
        self.addr_list.append(client_address)
        self.requests_queue[client_address] = []
        self.logger.info(f'Accepted new connection from {client_address}')

    def handle_disconnection(self, client_socket):
        idx = self.sockets_list.index(client_socket)
        self.logger.info(f'Connection with {self.addr_list[idx]} has been closed')
        del self.requests_queue[self.addr_list[idx]]
        del self.sockets_list[idx]
        del self.addr_list[idx]

    def verify_request(self, request_data):
        return True

    def non_blocking_request(self, request_data, client_addr):
        if self.verify_request(request_data):
            
            new_request = RequestClass(request_data)
            self.requests_queue[client_addr].append(new_request)

          
    #        client_socket = self.sockets_list[self.addr_list.index(client_addr)]
    #        try:
    #            self.send(client_socket, request_data)
    #        except:
    #            raise
    #    else:
    #        raise

    #def finish_request(self, data, client_addr):
    #    finished_request = self.requests_queue[client_addr].pop(0)
    #    finished_request.responce = data
    #    finished_request.DONE = True

    #def blocking_request(self, request_data, client_addr):
    #    client_socket = self.sockets_list[self.addr_list.index(client_addr)]
    #    try:
    #        self.send(client_socket, request_data)
    #    except:
    #        raise
    #    return responce

    def listen(self):
        #find the socket where reading is happening
        read_sockets, _, exception_sockets = select.select(self.sockets_list, [], self.sockets_list, 0.5)
        for notified_socket in read_sockets:
            #new connection
            if notified_socket == self.server_socket:
                self.handle_connection()
            
            #new message
            else:
                income_data = self.recv(notified_socket)
                if income_data is False:
                    # client disconnected
                    self.handle_disconnection(notified_socket)
                    continue

                client_addr = self.addr_list[self.sockets_list.index(notified_socket)]
                self.logger.debug(f'recv from {client_addr}')
                #self.finish_request(income_data, client_addr)

        for notified_socket in exception_sockets:
            # client disconnected violently
            self.handle_disconnection(notified_socket)
        
        if not (read_sockets, _, exception_sockets):
            pass

    def serve_forever(self):
        while self.active:
            self.listen()

    def start(self):
        threading.Thread(target=self.serve_forever, daemon=True).start()

    def 