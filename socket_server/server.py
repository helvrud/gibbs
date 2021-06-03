import server_client_class

server = server_client_class.SocketServer(IP = '127.0.0.1', PORT = 10010)

server.start()

server.server_loop()

