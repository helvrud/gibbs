from socket_server import SocketServer

server = SocketServer('127.0.0.1', 10001)
server.start()
server.loop()