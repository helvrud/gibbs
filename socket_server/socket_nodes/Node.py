#%%
import asyncio
import socket
import logging
import pickle
import sys
import threading
from time import sleep

#import patch_asyncio

logging.basicConfig(stream=open('log', 'w'), level=logging.DEBUG)
logger = logging.getLogger('Node')

class BaseNode:
    connected : bool = False
    IP : str
    PORT : int

    def __init__(self, IP,PORT) -> None:
        self.IP =IP
        self.PORT = PORT
        logger.debug('Initialized')

    async def connect(self):
        self.sock_reader, self.sock_writer = await asyncio.open_connection(self.IP, self.PORT)
        self.connected = True
        logger.debug('Connected')
        return True

    async def event_loop(self):
        await self.connect()
        while self.connected:
            logger.debug('\nListening...')
            data = await self.recv_raw()
            if data == False:
                self.handle_disconnection()
                break
            else:
                await self.handle_request(data)

    async def execute(self, request):
        logger.debug('Execute...', end ='')
        result = eval(request)
        logger.debug('Done', result)
        return result

    async def verify(self, request):
        return True

    async def handle_request(self, request):
        result = await self.execute(request)
        await self.send_raw(result)

    async def recv_raw(self):
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
        logger.debug('Sending...', end='')
        HEADER_LENGTH = 10
        msg = pickle.dumps(data)
        msg = bytes(f"{len(msg):<{HEADER_LENGTH}}", 'utf-8')+msg
        self.sock_writer.write(msg)
        logger.debug('Done')

    def handle_disconnection(self):
        logger.debug('Disconnected from server')
        self.connected = False

    def run(self):
        asyncio.run(self.event_loop())


if __name__=="__main__":
    node = BaseNode('127.0.0.1', 10000)
    node.run()
