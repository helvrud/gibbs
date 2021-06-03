#%%
import server_client_class

client = server_client_class.Client(IP = '127.0.0.1', PORT = 10010)

client.connect()

#%%
client.send_addr()

# %%
msg = server_client_class.Message()
msg.data = 'hi'
msg.receiver = client.addr
client.send_object(msg)

ans=client.recv_object()

# %%
# %%
clientB = server_client_class.Client(IP = '127.0.0.1', PORT = 10010)

clientB.connect()

# %%
clientB.disconnect()
# %%
msg = server_client_class.Message()
msg.data = 'hi'
msg.receiver = clientB.addr
client.send_object(msg)

# %%
ans= clientB.recv_object()
# %%
ans.data
# %%
