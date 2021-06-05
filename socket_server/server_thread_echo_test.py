#%%
from socket_server import Client
from socket_server import Server
#%%
server = Server.SocketServer('127.0.0.1', 10001)
server.start()
server_thread = server.loop_thread()
server_thread.start()
#%%
client = Client('127.0.0.1', 10001)
client.connect()
client.echo_test()
client.send_message('\STOP_SERVER','host')
server_thread.join()
