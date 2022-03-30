from ion_pair_monte_carlo import MonteCarloPairs
import logging
import socket_nodes
try: from tqdm import trange
except: trange = range

socket_nodes.set_params(LOG_REQUESTS_INFO = True)


from routines import sample_to_target
import time
#logger = logging.getLogger("socket_nodes")
#logger = logging.getLogger(__name__)



class gel():
    start_time = time.time()
    c_s = 0.1 # mol/l
    MPC = 10
    bond_length = 1.0 # used for constructing the network during the gel initialization
    A = 3*3**(0.5)/4 # The coefficient which relates volume per chain in the diamond lnetwork with the lenght of the chain R^3 = V*A
    Rmax = MPC * bond_length
    Vmax = Rmax**3/A
    Vmax *= 16 
    
    lB = 0 # 0 means no electrostatic interaction. Default is 2
    sigma =0 # 0 means no static interaction
    alpha = 0.5
    Ncl = 500


    target_sample_size=200# number of samples,
    timeout = 1*3600 - (time.time() - start_time) # seconds
    #save_file_path = output_dir/output_fname

    
    Vbox = Vmax*0.5
    Vgel = Vbox*0.7
    Vout = Vbox*0.3


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
            
            self.server, self.pid_gel, self.pid_out = socket_nodes.create_server_and_nodes(name = 'test', box_l_gel = self.box_l_gel, box_l_out = self.box_l_out, alpha = self.alpha, MPC = self.MPC)
            
            self.MC = MonteCarloPairs(self.server)
            Ncl_gel = int(self.Ncl*self.Vgel/(self.Vout+self.Vgel))
            Ncl_out = int(self.Ncl*self.Vout/(self.Vout+self.Vgel))
            Ncl_out += self.Ncl - (Ncl_gel + Ncl_out)
            self.MC.populate([Ncl_gel, Ncl_out])
            self.server("minimize_energy()", [0,1])
            #logger.info("#################################")
            
    def equilibrate(self) :
        eq_params = {'timeout_eq':120, 'rounds_eq':10, 'mc_steps_eq':100, 'md_steps_eq':1000}
        self.MC.equilibrate(**eq_params)
        
    def NN(self):
        """
        This function  returns the number of mobile anion particles in gel and in reservoir as a list
        """
        Nanion_gel  = g.server("system.number_of_particles(0)", [0])[0].result()     
        Ncation_gel = g.server("system.number_of_particles(1)", [0])[0].result()
        Nanion_out  = g.server("system.number_of_particles(0)", [1])[0].result()
        Ncation_out = g.server("system.number_of_particles(1)", [1])[0].result()

        Ngel_neutral      = g.server("system.number_of_particles(2)", [0])[0].result()          
        Ngel_anion        = g.server("system.number_of_particles(3)", [0])[0].result()
        Ngel_node_neutral = g.server("system.number_of_particles(4)", [0])[0].result()
        Ngel_node_anion   = g.server("system.number_of_particles(5)", [0])[0].result()
        print (f'Ncl_gel {Nanion_gel}\n Nna_gel{Ncation_gel}\n Ngel_neutral{Ngel_neutral}\n Ngel_anion{Ngel_anion}\n Ngel_node_neutral{Ngel_node_neutral}\n Ngel_node_anion {Ngel_node_neutral}\n Ncl_out{Nanion_out}\n Nna_out{Ncation_out}\n')
        return [Nanion_gel, Nanion_out]
        
        
g = gel(run = True)
#g.MC.equilibrate(1,1,1)

g.MC = MonteCarloPairs(g.server)

#g.MC.populate([40]*2)

#z = g.server("minimize_energy()", [0,1])
if g.lB: 
    g.server('enable_electrostatic()', [0, 1])
    z = g.server("minimize_energy()", [0,1])
#self.MC.sample_pressures_to_target_error()

#result = g.MC.sample_all(200,1)

#
#g.MC.sample_zeta_to_target_error()
#g.MC.sample_particle_count_to_target_error()

#g.MC.sample_pressures_to_target_error()

#result = g.MC.sample_all(200,10)
