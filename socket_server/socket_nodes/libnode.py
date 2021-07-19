import asyncio
import logging
import pickle
#import patch_asyncio
import sys
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger('Node')

class BaseNode:
    """Class implementing a node connected to a server, 
    capable of to handle request. Can be used for distributed computing.
    Connected node listens to the socket for requests and sends back 
    the results when one is available
    """    
    connected : bool = False
    IP : str
    PORT : int

    def __init__(self, IP : str, PORT : int) -> None:
        """Initialize the node, without connection
        Args:
            IP (str), PORT (int): Must be the same as on the server side
        """        
        self.IP =IP
        self.PORT = PORT
        logger.info(f'Initialized with {self.IP}, {self.PORT}')

    async def connect(self) -> bool:
        """Connects to the server

        Returns:
            [bool]: True if success
        """        
        self.sock_reader, self.sock_writer = await asyncio.open_connection(self.IP, self.PORT)
        self.connected = True
        logger.info('Connected to the server')
        return True

    async def event_loop(self):
        """The main loop of the node
        0)Connects to the server
        1)Listen for incoming data
        2)Process request
        3)Send the results back
        """        
        await self.connect()

        #while the note is still connected
        while self.connected:
            logger.debug('\nListening...')
            #get the data from the socket
            data = await self.recv_raw()
            #if no data -> connection is lost
            if data == False:
                self.handle_disconnection()
                break
            else:
                await self.handle_request(data)

    async def execute(self, request):
        """Trying to execute the request, the method has to be overridden 
        for child classes by default tries to eval(request)
        
        Args:
            request (object): valid request

        Returns:
            object: execution result
        """        
        result = eval(request)
        logger.debug('Request is executed')
        return result

    async def verify(self, request) -> bool:
        """Verify if request is correct, 
        the method has to be overridden if some checks needed

        Args:
            request (object): request

        Returns:
            bool: True if request is valid
        """        
        return True

    async def handle_request(self, request):
        """Handles request from server, send the result back when available
        Args:
            request (object): [description]
        """
        #if request pass sanity check        
        if await self.verify(request):
            result = await self.execute(request)
        #if not send the error back
        else:
            result = 'Invalid request'
        await self.send_raw(result)

    async def recv_raw(self):
        """Receiving protocol is implemented here, allows to send any 
        pickable python object, can be overridden

        Args:
            node_socket (socket): node's socket
        """ 
        HEADER_LENGTH = 10
        try:
            message_header = await self.sock_reader.read(HEADER_LENGTH)
            #no data -> client closed a connection
            if not len(message_header):
                return False
            message_length = int(message_header.decode('utf-8').strip())
            serialized_data = await self.sock_reader.read(message_length)
            data = pickle.loads(serialized_data)
            return data
        except Exception as e:
            logger.error(e)
            return False
    
    async def send_raw(self, data):
        """Sending protocol is implemented here, allows to send any 
        pickable python object, can be overridden

        Args:
            node_socket (socket): node's socket
            data (object): data to send
        """
        HEADER_LENGTH = 10
        msg = pickle.dumps(data)
        msg = bytes(f"{len(msg):<{HEADER_LENGTH}}", 'utf-8')+msg
        self.sock_writer.write(msg)
        logger.debug("Request's result is sent")

    def handle_disconnection(self):
        """Can be overridden to implement extra actions on disconnection
        """        
        logger.warning('Disconnected from server')
        self.connected = False

    def run(self):
        """Run the node by calling this method
        Blocking call, use threading or multiproccessing, 
        Consider using self.event_loop() for asynchronous code
        """        
        asyncio.run(self.event_loop())



class ExecutorNode(BaseNode):
    """Inherited from BaseNode, allows to define executor, 
    by instantiating ExecutorClass
    requirements to ExecutorClass:
    should provide three methods:
        __init__()
        execute(request) -> result
        verify(request) -> bool

    it is advised to inherited from BaseExecutorClass from libexecutor.py

    """    
    def __init__(self, IP : str, PORT : int, ExecutorClass, *args, **kwargs) -> None:
        """Initialize the node, without connection, instantiates ExecutorClass

        Args:
            IP (str): [description]
            PORT (int): [description]
            ExecutorClass ([type]): [description]
        """        
        super().__init__(IP, PORT)
        self.Executor = ExecutorClass(*args, **kwargs)
    async def execute(self, request):
        return self.Executor.execute(request)
    async def verify(self, request):
        return self.Executor.verify(request)
