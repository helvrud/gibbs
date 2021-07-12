import socket
import logging
import pickle
import select
from enum import Enum, auto
from typing import List
import sys

logging.basicConfig(stream=open('log', 'w'), level=logging.DEBUG)
logger = logging.getLogger('Terminal')



class RequestStatus(Enum):
    """
    Possible request status
    """    
    InProgress = auto()
    Done = auto()
    #ErrorOccurred = auto()
    #Timeout = auto()


class NoResult:
    pass


class BaseRequest:

    """
    Request class gives access to a result of an request from BaseTerminal class
    holds NoResult at initialization until acquire the result of the request
    from the node

    Use self.result() to wait for result, if not threaded can block the program
    """    

    def __init__(self, request) -> None:
        """Initializes request

        Args:
            request (pickleable object): request data
        """        
        self.request = request
        self.status = RequestStatus.InProgress
        self._result = NoResult
    
    def __bool__(self):
        """Check if request is done

        Returns:
            [bool]: True if request status is done
        """        
        return self.status == RequestStatus.Done
    
    def result(self):
        """Waits for the result of the request and returns it

        Returns:
            [pickleable object]: request's result
        """        
        while True:
            if self.status == RequestStatus.Done:
                return self._result





class BaseConnectedNode:
    """Contains information about connected node, manages requests from 
    'mainframe' terminal object (socket server)

    requests : List[BaseRequest] - list of queued requests FIFO

    """    
    requests : List[BaseRequest] = []
    def __init__(self, socket, address) -> None:
        self.socket = socket
        self.address = address
        logger.debug(f'New node registered\n address: {address}')


    def is_busy(self):
        return bool(self.requests)


    def add_request(self, request_data):
        """add request to a queue, so that server side of the socket knows about
        it, returns request object allowing to track the results of the request,
        put the request to the end of FIFO

        Returns:
            [BaseRequest]: Request object
        """     
        Request = BaseRequest(request_data)
        self.requests.append(Request)
        logger.debug(f'New request added\n request_data: {request_data}')   
        return Request


    def finish_request(self,result):
        """Set result to the fist request object in the queue and pop it, 
        now the result can be accessed with Request.result()

        """
        logger.debug(f'Request finished')
        Request = self.requests.pop(0)
        Request._result = result
        Request.status = RequestStatus.Done
        logger.debug(f'{Request.request} -> {result}')






class BaseTerminal():
    """Interface to controll multiple instancess of something that has 
    python-bindings, allowing to instantiates an object multiple times 
    isolated, interproccess communication between nodes and terminal 
    happens via TCP protocol
    """    
    active : bool
    nodes : List[BaseConnectedNode] = [] ##should refactored into collection

    def __init__(self, IP : str = '127.0.0.1', PORT : int = 0) -> None:
        """Initialize an object, set PORT to zero to allow OS assign it

        Args:
            IP ([str]): host ip
            PORT ([int]): port to open
        """    
        self.IP = IP
        self.PORT = PORT
        logger.debug(f'Initialized with {IP}, {PORT}')


    def setup(self):
        """setup the TCP socket server to work as a terminal that gather 
        info from the nodes
        """        
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.setblocking(0)
        server_socket.bind((self.IP, self.PORT))
        server_socket.listen()
        self.active = True
        self.socket = server_socket

        logger.debug(f'Listening to {self.IP} ...')


    def handle_connection(self):
        """handels connection of a new node, add it to a list of connected nodes
        """        
        node_socket, node_address = self.socket.accept()
        Node = BaseConnectedNode(node_socket, node_address)
        self.nodes.append(Node)
        
        logger.info(f'Accepted new connection from {node_address}')
        logger.debug(f'Nodes connected: {len(self.nodes)}')


    def handle_disconnection(self, node_id : int):
        """Disconnection of the node, deletes it from the list of connected 
        nodes self.nodes

        Args:
            node_id (int): node index in the list of connected nodes (self.nodes)
        """        
        logger.warning(f'Connection with {self.nodes[node_id].address} has been closed')
        
        del self.nodes[node_id]

    
    def handle_income(self, income_data, node_id : int):
        """Handle an income, by finnishing FIFO request of the node

        Args:
            income_data ([type]): responce from the node
            node_id (int): node index in the list of connected nodes (self.nodes)
        """        
        
        logger.debug(f'Handle income from {self.nodes[node_id].address}\n data:{income_data}')
        
        self.nodes[node_id].finish_request(income_data)


    def listen(self):
        """
        TCP server listens to several nodes (TCP Clients) and new connections
        invokes handlers depending on the event
        """        
        sockets_list = [node.socket for node in self.nodes]+[self.socket]
        #find the socket where reading is happening
        read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)
        for notified_socket in read_sockets:
            logger.debug(f'Notified socket: {notified_socket}')
            #new connection
            if notified_socket == self.socket:
                self.handle_connection()
            
            #new message
            else:
                #find the Node sending the data
                node_id = self.get_node_idx_by_socket(notified_socket)#cumbersome
                #recv data
                income_data = self.recv_raw(notified_socket)
                # client disconnected
                if income_data is False:
                    self.handle_disconnection(node_id)
                    continue
                #handle income data
                self.handle_income(income_data, node_id)
        
        #error
        for notified_socket in exception_sockets:
            # client disconnected violently
            self.handle_disconnection(notified_socket)
        
        #timeout
        if not (read_sockets, _, exception_sockets):
            logging.debug('Timeout')
            pass


    def request(self, request_data, node_id : int) -> BaseRequest:
        """Makes a request to a node with index node_id, returns an instance of
         the BaseRequest class, which allows to collect the result later

        Args:
            request_data ([type]): [description]
            node_id (int): node index in the list of connected nodes (self.nodes)

        Returns:
           [BaseRequest]: Request object, get the result with _.result()
        """
        logger.debug('Creating new request...')        
        Request =  self.nodes[node_id].add_request(request_data)
        node_socket = self.nodes[node_id].socket
        self.send_raw(node_socket, request_data)
        return Request


    def wait(self, node_id : int):
        """Waits for the node to finnish all the requests

        Args:
            node_id (int): node index in the list of connected nodes (self.nodes)
        """        
        while self.nodes[node_id].is_busy()==False:
            pass


    def wait_all(self):
        """Waits for the all nodes to finnish all the requests

        Args:
            node_id (int): node index in the list of connected nodes (self.nodes)
        """
        someone_is_busy = any([node.is_busy() for node in self.nodes])
        while someone_is_busy:
            pass


    def send_raw(self, node_socket, data):
        HEADER_LENGTH = 10
        msg = pickle.dumps(data)
        msg = bytes(f"{len(msg):<{HEADER_LENGTH}}", 'utf-8')+msg
        node_socket.send(msg)
    

    def recv_raw(self, node_socket):
        HEADER_LENGTH = 10
        try:
            message_header = node_socket.recv(HEADER_LENGTH)
            #no data -> client closed a connection
            if not len(message_header):
                return False
            message_length = int(message_header.decode('utf-8').strip())
            serialized_data = node_socket.recv(message_length)
            data = pickle.loads(serialized_data)
            return data
        except Exception as e:
            logger.error(e)
            return False


    def loop_forever(self):
        while self.active:
            self.listen()

    
    def shutdown(self):
        self.active == False


    ##Should not be implemented here
    def get_node_idx_by_addr(self, address):
        addrs = [Node.address for Node in self.nodes]
        idx = addrs.index(address)
        return idx
    
    def get_node_idx_by_socket(self, address):
        sockets_ = [Node.socket for Node in self.nodes]
        idx = sockets_.index(address)
        return idx