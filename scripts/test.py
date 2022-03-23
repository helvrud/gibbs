from ion_pair_monte_carlo import MonteCarloPairs
import socket_nodes
from routines import sample_to_target
import time

class gel():
    start_time = time.time()
    c_s = 0.1 # mol/l
    MPC = 10
    bond_length = 1.0 # used for constructing the network during the gel initialization
    A = 3*3**(0.5)/4 # The coefficient which relates volume per chain in the diamond lnetwork with the lenght of the chain R^3 = V*A
    Rmax = MPC * bond_length
    Vmax = Rmax**3/A
    
    lB = 0 # 0 means no electrostatic interaction
    sigma =0 # 0 means no static interaction
    alpha = 0.
    Ncl = 10


    target_sample_size=200# number of samples,
    timeout = 1*3600 - (time.time() - start_time) # seconds
    #save_file_path = output_dir/output_fname

    

    Vgel = Vmax*0.5
    Vout = 100

    def __init__(self, run=False):
    
    
        self.box_l_gel = self.Vgel**(1./3)
        self.box_l_out = self.Vout**(1./3)
        
        
        #arg_list_gel = ['-l', box_l_gel, '--gel' , '-MPC', self.MPC, '-bond_length', self.bond_length, '-alpha', self.alpha, '-log_name', 'test_gel.log'] + ['--no_interaction']*bool(self.lB)
        #arg_list_out = ['-l', box_l_out, '--salt', '-log_name', 'test_out.log'] + ['--no_interaction']*bool(self.lB)
        self.name = 'gibbs_Vgel{:.2f}_Vout{:.2f}_Ncl{}'.format(self.Vgel, self.Vout, self.Ncl)
        if self.alpha != 1.: self.name+='_alpha{:.2f}'.format(self.alpha)
        if self.lB == 0.:    self.name+='_lB{:.0f}'.format(self.lB)
        if self.sigma == 0.: self.name+='_sigma{:.0f}'.format(self.sigma)
        if run:
            
            self.server = socket_nodes.create_server_and_nodes(name = self.name, box_l_gel = self.box_l_gel, box_l_out = self.box_l_out, alpha = self.alpha, lB=self.lB, sigma=self.sigma, MPC = self.MPC)
            #self.server("minimize_energy()", [0,1])
            
            

g = gel(run = True)
#g.MC.equilibrate(1,1,1)

g.MC = MonteCarloPairs(g.server)
g.MC.populate([g.Ncl]*2)
z = g.server("minimize_energy()", [0,1])
g.MC.sample_pressures_to_target_error()




if g.lB: 
    g.server('enable_electrostatic()', [0, 1])
    z = g.server("minimize_energy()", [0,1])
#self.MC.sample_pressures_to_target_error()

result = g.MC.sample_all(200,1)

#g.MC.sample_pressures_to_target_error()
#g.MC.sample_zeta_to_target_error()
#g.MC.sample_particle_count_to_target_error()

