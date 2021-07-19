from collections import namedtuple
import threading
import subprocess
from socket_nodes import Server


server = Server('127.0.0.1', 0)
threading.Thread(target=server.run, daemon=True).start()

MC_Init_Data = namedtuple('MC_Init_Data', ['energy', 'particles', 'box_l'])
def get_mc_init_data():
    system_state_request=server([
        "float(system.analysis.energy()['total'])",
        "[list(system.part.select(type=0).id), list(system.part.select(type=1).id)]",
        "system.box_l"
        ],[0,1])
    for i in range(2):
        energy = [result[0] for result in system_state_request[i].result()]
        part_ids = [result[1] for result in system_state_request[i].result()]
        box_l = [result[2] for result in system_state_request[i].result()]

    return energy, part_ids, box_l

    
    
