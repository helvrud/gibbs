#%%
import espressomd
required_features = ["LENNARD_JONES"]
espressomd.assert_features(required_features)
from socket_server import ObjectSocketInterface
client = ObjectSocketInterface('127.0.0.1', 10007)
client.create_object(espressomd.System, box_l=[40, 30, 20])
#%%
client.connect()
client.loop()
#%%
res = eval("client._object.part.add(pos = [0,0,0])")
# %%
res
# %%
