import socket
import select
import pickle
import time
import sys

from .Message import Message

HEADER_LENGTH = 10

class ServerBase():
    sockets_list = []
    addr_list = []
    server_socket = None
    _active = True
    logs = []
    select_timeout = 0.5

    def __init__(self, IP, PORT) -> None:
        self.IP = IP
        self.PORT = PORT

    def setup(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #reuse blocked sockets
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.settimeout(30.0)

        server_socket.bind((self.IP, self.PORT))
        self.logs.append(f'HOST: Listening to {self.IP} ...')
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

    def _send_object(self, client_socket, data):
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
            self.logs.append("HOST: The data isn't wrapped into the Message class")
            return None

    def send_message(self, data, client_addr):
        client_socket = self.sockets_list[self.addr_list.index(client_addr)]
        msg = Message(data = data, sender = 'host', receiver = client_addr)
        self._send_object(client_socket, msg)

    def _income_msg_handle(self, msg):
        self.logs.append(f"HOST: [INCOME MESSAGE] from {msg.sender}")
        data = msg.data
        self.logs.append(str(data))
        if isinstance(data,str):
            if data == "\STOP_SERVER":
                self._active = False
            elif data == "\ECHO":
                self.send_message('\ECHO_OK', msg.sender)
    
    def _forwarding_msg_handle(self, msg):
        client_addr = msg.receiver
        if client_addr in self.addr_list:
            client_socket = self.sockets_list[self.addr_list.index(client_addr)]
            self.logs.append(f"HOST: [FORWARDING MESSAGE] from {msg.sender} to {client_addr}")
            self._send_object(client_socket, msg)
        else:
            self.logs.append(f"HOST: Client is not found, forwarding failed")
            self.send_message('\FORWARDING_FAILED', msg.sender)

    def _new_conn_handle(self):
        client_socket, client_address = self.server_socket.accept()
        self.sockets_list.append(client_socket)
        self.addr_list.append(client_address)
        self.logs.append(f'HOST: Accepted new connection from {client_address}')
        #sending to the connected client his address on the server
        #self._send_object(client_socket, client_address)
        msg = pickle.dumps(client_address)
        msg = bytes(f"{len(msg):<{HEADER_LENGTH}}", 'utf-8')+msg
        client_socket.send(msg)

    def _disconn_handle(self, client_socket):
        idx = self.sockets_list.index(client_socket)
        self.logs.append(f'HOST: Connection with {self.addr_list[idx]} has been closed')
        del self.sockets_list[idx]
        del self.addr_list[idx]

    def _stop_server_routine(self, timeout = 3):
        self.logs.append('HOST: The server will be stopped')
        #broadcast the message that server is stopped
        for client_addr in self.addr_list[1:]:
            self.send_message('\STOP_SERVER', client_addr)
        if timeout is not None: time.sleep(timeout)
        self.server_socket.close()
        self.flush_log()
        sys.exit()
        
    def listen(self):
        #find the socket where reading is happening
        read_sockets, _, exception_sockets = select.select(self.sockets_list, [], self.sockets_list, self.select_timeout)
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
        
        if not (read_sockets, _, exception_sockets):
            pass

    def flush_log(self):
        while self.logs:
            self.logs.pop(0)


class SocketServer(ServerBase):
    sending_queue =  [] #(client_addr, data)
    last_income = None
    
    def _client_is_busy(self, client_addr):
        if self.sending_queue:
            busy_addrs = set([item[0] for  item in self.sending_queue])
            return client_addr in busy_addrs
        else:
            return False

    def _del_last_occur_client(self, client_addr):
        idx = None
        for idx, queue_item in enumerate(self.sending_queue):
            if queue_item[0] == client_addr:
                break
        del self.sending_queue[idx]
    
    def send_request(self, data, client_addr,):
        self.send_message(data, client_addr)
        while self._client_is_busy(client_addr):
            pass
        time.sleep(0.05)
        result = self.last_income.data
        self.last_income = None
        return result
    
    def _send_object(self, client_socket, data):
        client_addr = self.addr_list[self.sockets_list.index(client_socket)]
        if self._client_is_busy(client_addr):
            self.sending_queue.append((client_addr, data))
            self.logs.append(f'HOST: Client f{client_addr} is busy')
            #print(f'HOST: Client f{client_addr} is busy')#!!!
        else:
            self.sending_queue.append((client_addr, data))
            super()._send_object(client_socket, data)

    def _recv_object(self, client_socket):
        client_addr = self.addr_list[self.sockets_list.index(client_socket)]
        if self._client_is_busy(client_addr):
            self._del_last_occur_client(client_addr)
        self.last_income = super()._recv_object(client_socket)
        return self.last_income

    def _send_from_queue(self, timeout = 0.1):
        if self.sending_queue:
            queue = self.sending_queue.copy()
            self.sending_queue = []
            for queue_item in queue:
                time.sleep(timeout)
                client_addr, data = queue_item
                client_socket = self.sockets_list[self.addr_list.index(client_addr)]
                self.logs.append(f'HOST: Send to f{client_addr} from queue')
                self._send_object(client_socket, data)

    def serve_loop(self):
        while self._active:
            self.listen()
            self.flush_log()
            self._send_from_queue()
            self.flush_log()
        else:
            time.sleep(self.loop_timeout)
            while self.sending_queue:
                self._send_from_queue()
            self.flush_log()
            self._stop_server_routine()

    def start(self):
        from threading import Thread
        self.flush_log()
        p1 = Thread(target=self.serve_loop, daemon=True)
        p1.start()
        return p1




    

        


