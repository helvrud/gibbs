from ion_pair_monte_carlo import MonteCarloPairs
import logging, os
import socket_nodes, getpass, time, pprint
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


    
    lB = 0 # 0 means no electrostatic interaction. Default is 2
    sigma =0 # 0 means no static interaction
    alpha = 1.0
    

    eq_steps = 100
    N_Samples=10# number of samples,
    timeout = 1 # hours
    #save_file_path = output_dir/output_fname

    

    USERNAME = getpass.getuser()
    #if USERNAME == 'alexander': USERNAME = "kazakov"

    hd = '/home/{0}'.format(USERNAME)               # home directory on conteiner
    wd = hd+'/gibbs/'                                  # working directory on conteiner
    pypresso = hd+'/espresso/espresso/es-build/pypresso '
    
    def __init__(self, Vbox, Vgel, Ncl, run=False):



        self.Rmax = self.MPC * self.bond_length
        self.Vmax = self.Rmax**3/self.A
        self.Vmax *= 16 
        self.Vbox = Vbox
        self.Vgel = Vgel
        self.Ncl = Ncl
        self.Vout = Vbox - Vgel


        self.box_l_gel = self.Vgel**(1./3)
        self.box_l_out = self.Vout**(1./3)
        
        self.__str__()
        #arg_list_gel = ['-l', box_l_gel, '--gel' , '-MPC', self.MPC, '-bond_length', self.bond_length, '-alpha', self.alpha, '-log_name', 'test_gel.log'] + ['--no_interaction']*bool(self.lB)
        #arg_list_out = ['-l', box_l_out, '--salt', '-log_name', 'test_out.log'] + ['--no_interaction']*bool(self.lB)
        

            

    def __str__(self):

        #~ self.name = self.name+'_pCl{:.2f}'.format(self.p['Cl'])+'_lB'+str(self.lB)+'_sigma'+str(self.sigma)

        
        self.name = 'gibbs_Vgel{:.2f}_Vout{:.2f}_Ncl{}'.format(self.Vgel, self.Vout, self.Ncl)
        if self.alpha != 1.: self.name+='_alpha{:.2f}'.format(self.alpha)
        if self.lB == 0.:    self.name+='_lB{:.0f}'.format(self.lB)
        if self.sigma == 0.: self.name+='_sigma{:.0f}'.format(self.sigma)

            
        if self.N_Samples != 100: self.name += '_N'+str(self.N_Samples)

        self.fname = 'data/'+self.name
        self.fnameout = self.fname+".out"
        self.fnamepkl = self.fname+".pkl"
        self.fnamepy = self.fname+".py"

        # ~ self.fnamerun     = self.fname+'.run'
        self.fnameqsub    = self.fname+'.qsub'
        self.fnameqsubout = self.fname+'.qsubout'
        self.fnameqsuberr = self.fname+'.qsuberr'

        return self.name          




    def qsubfile(self, mem = '2gb', walltime = 24):
        # ~ self.WD = '/storage/praha1/home/kvint/hydrogel/scripts/'
        # this part prepares the scripts for qsub to run ot tarkil    WD = '/storage/brno2/home/{}/mv/'.format(USERNAME)
        
        
                                # working directory on skirit

        qsubfile = open(self.fnameqsub,'w')
        qsubfile.write('#!/bin/bash\n');
        qsubfile.write('#PBS -N '+self.name.replace('/','_')+'\n');
        #~ qsubfile.write('#$ -l nodes=1:ppn=1\n');
        #~ qsubfile.write('#$ -l walltime=200:00:00\n');
        qsubfile.write('#PBS -l mem='+mem+'\n');
        qsubfile.write('#PBS -l ncpus=1\n');
        qsubfile.write('#PBS -l walltime='+str(int(walltime))+':0:0\n');
        qsubfile.write('#PBS -m ae\n');
        qsubfile.write('#PBS -e '+self.WD+self.fnameqsuberr+'\n');
        qsubfile.write('#PBS -o '+self.WD+self.fnameqsubout+'\n');
        # ~ qsubfile.write('. /storage/praha1/home/kvint/.bashrc\n');
        #qsubfile.write('cd '+self.WD+'\n');

        #qsubfile.write('/storage/praha1/home/kvint/hydrogel/scripts/espresso/es-build/pypresso '+self.fnamepy+'\n');
        #qsubfile.write('rm /storage/brno2/home/kvint/mv/'+self.fname+'.qsubout\n')
        #qsubfile.write('rm /storage/brno2/home/kvint/mv/'+self.fname+'.qsuberr\n')
        qsubfile.write('singularity exec -B '+self.HD+':'+self.hd+' '+self.HD+'/ubuntu.img '.format(self.USERNAME) +self.pypresso+' '+self.WD+self.fname+'.py\n');
        qsubfile.close()

    def seedscript(self):

        output = []
        output.append("#!espresso/es-build/pypresso")
        # ~ output.append("#!venv/bin/python")
        output.append("import sys, os")
        output.append("os.chdir('/home/{}/gibbs/scripts')".format(self.USERNAME))
        output.append("sys.path.append('/home/{}/gibbs/scripts')".format(self.USERNAME))
        output.append("from espressomd import reaction_ensemble")
        output.append("from gel import gel")


        output.append("g =gel()")
        output.append("g.lB = "+str(self.lB))


        # ~ output.append("g.alpha_ini = "+str(self.alpha_ini))
        output.append("g.Vbox = "+str(self.Vbox))
        output.append("g.Vgel = "+str(self.Vgel))
        output.append("g.eq_steps = "+str(self.eq_steps))


        output.append("g.N_Samples = "+str(self.N_Samples))
        output.append("g.run()")

        infile = open(self.fnamepy, 'w')
        for line in output:
            infile.write(line+'\n')
        infile.close()
        os.chmod(self.fnamepy, 0o774)
        
    def send2metacentrum(self, run = False, walltime = 2, mem = '100mb', hostname = 'skirit'):
        #self.WD = '/storage/praha1/home/kvint/mv/'
        if hostname == 'skirit':
            self.HD = '/storage/brno2/home/{0}'.format(self.USERNAME) # home directory on skirit
            self.WD = self.HD+'/gibbs/scripts/'                                  # working directory on skirit
        else:
            self.HD = '/storage/praha1/home/{0}'.format(self.USERNAME) # home directory on skirit
            self.WD = self.HD+'/gibbs/scripts/'                                  # working directory on skirit

        # ~ self.runfile()
        self.seedscript()
        self.qsubfile(walltime = walltime, mem = mem)

        # ~ os.system("scp " + self.fnamepkl  + " skirit.metacentrum.cz:"+self.WD+"data/")
        # ~ os.system("scp salt.py base.py gel.py "+hostname+".metacentrum.cz:"+self.WD)
        os.system("scp " + self.fnameqsub + " "+hostname+":"+self.WD+self.fnameqsub)
        os.system("scp " + self.fnamepy  + " " +hostname+":"+self.WD+self.fnamepy)

    def run(self):
        tini = time.time()
        print(self) # this updates the filenames

        self.server, self.pid_gel, self.pid_out = socket_nodes.create_server_and_nodes(name = self.name, box_l_gel = self.box_l_gel, box_l_out = self.box_l_out, alpha = self.alpha, MPC = self.MPC)


        self.MC = MonteCarloPairs(self.server)
        Ncl_gel = int(self.Ncl*self.Vgel/(self.Vout+self.Vgel))
        Ncl_out = int(self.Ncl*self.Vout/(self.Vout+self.Vgel))
        Ncl_out += self.Ncl - (Ncl_gel + Ncl_out)
        self.MC.populate([Ncl_gel, Ncl_out])
        self.minimize_energy()            
        self.equilibrate(eq_steps = 10)

        if self.lB:
            z = self.server(f'enable_electrostatic(lB = {self.lB})', [0, 1])
            z = self.server("minimize_energy()", [0,1])

        self.equilibrate()
        self.sample()

        #self.Pearson(keys = self.keys['md']+self.keys['re'])
        self.uptime = time.time() - tini
        #self.save()    
                
    def equilibrate(self) :
        eq_params = {'timeout_eq':60, 'rounds_eq':self.eq_steps, 'mc_steps_eq':1000, 'md_steps_eq':10000}
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
    def sample(self):
        sample_d = g.MC.sample_all(self.N_Samples,self.timeout)
        return sample_d

    def minimize_energy(self):
        z = g.server("minimize_energy()", [0,1])


g = gel(Vbox = 6158, Vgel = 4310, Ncl = 500)
g.send2metacentrum()
#g.qsubfile()












