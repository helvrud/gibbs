#%%
from socket_server import Client
#%%
client = Client('127.0.0.1', 10001)
#%%
client.connect()
# %%
client.send_message('hi','host')
# %%
client.send_message('hi',client.addr)

# %%
client.recv_message()
# %%
client.send_message('\STOP_SERVER', 'host')
# %%
client.echo_test()
# %%
