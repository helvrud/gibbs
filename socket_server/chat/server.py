import server_client_class

server = server_client_class.SocketServer(IP = '127.0.0.1', PORT = 10003)

server.start()

server.test_chat_loop()