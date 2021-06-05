#%%
import sys
import server_client_class


IP = '127.0.0.1'
PORT = 22223

clientA = server_client_class.Client(IP, PORT)
clientB = server_client_class.Client(IP, PORT)

# %%
import subprocess

subprocess.Popen(['python', 'server.py'], stdout=open('server.log','w'))

# %%
clientA.connect()
clientB.connect()
# %%
message_A_B = server_client_class.Message()
message_A_B.data = {'some' : ['python', 'object']}
message_A_B.sender = clientA.addr
message_A_B.receiver = clientB.addr
clientA.send_object(message_A_B)
#%%
clientB.recv_object()
# %%
message_A_S = server_client_class.Message()
message_A_S.data = 'STOP_SERVER'
message_A_S.sender = clientA.addr
message_A_S.receiver = 'host'
clientA.send_object(message_A_B)
# %%
