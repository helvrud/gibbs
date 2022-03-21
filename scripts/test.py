from ion_pair_monte_carlo import MonteCarloPairs
import socket_nodes
from routines import sample_to_target

python_executable = '/home/kvint/espresso/espresso/es-build/pypresso' 
script_name = 'run_node.py'

class gel():
    c_s = 0.1 # mol/l
    MPC = 10
    bond_length = 1.0 # used for constructing the network during the gel initialization
    A = 3*3**(0.5)/4 # The coefficient which relates volume per chain in the diamond lnetwork with the lenght of the chain R^3 = V*A
    Rmax = MPC * bond_length
    Vmax = Rmax**3/A
    
    lB = 0 # 0 means no electrostatic interaction
    sigma =0 # 0 means no static interaction
    alpha = 0.
    N_pairs = 10




    Vgel = Vmax*0.5
    Vout = 100

    def __init__(self, run=False):
    
    
        box_l_gel = self.Vgel**(1./3)
        box_l_out = self.Vout**(1./3)
        
        scripts = [script_name]*2
        arg_list_gel = ['-l', box_l_gel, '--gel' , '-MPC', self.MPC, '-bond_length', self.bond_length, '-alpha', self.alpha, '-log_name', 'test_gel.log'] + ['--no_interaction']*bool(self.lB)
        arg_list_out = ['-l', box_l_out, '--salt', '-log_name', 'test_out.log'] + ['--no_interaction']*bool(self.lB)
        
        if run:
            self.server = socket_nodes.create_server_and_nodes(
                scripts=scripts, args_list=[arg_list_gel, arg_list_out], python_executable=python_executable, connection_timeout_s = 2400,
                #stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                )
            #self.server("minimize_energy()", [0,1])
g = gel(run = True)
#g.MC.equilibrate(1,1,1)



g.MC = MonteCarloPairs(g.server)
g.MC.populate([g.N_pairs]*2)
g.server("minimize_energy()", [0,1])
#self.MC.sample_pressures_to_target_error()

#g.MC.sample_pressures_to_target_error()
#g.MC.sample_zeta_to_target_error()
#g.MC.sample_particle_count_to_target_error()

