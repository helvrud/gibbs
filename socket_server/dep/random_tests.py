#%%
import server_client_class

clientA = server_client_class.Client(IP = '127.0.0.1', PORT = 10029)
clientA.connect()

msg = server_client_class.Message()
msg.data = 'hi'
msg.receiver = clientA.addr
msg.sender = clientA.addr
clientA.send_object(msg)
# %%
echo =clientA.recv_object()
# %%
print(echo.data)
# %%
msg.receiver = ('127.0.0.1', 42556)
clientA.send_object(msg)
# %%
msg.receiver = 'host'
msg.data = 'STOP_SERVER'
clientA.send_object(msg)
# %%
