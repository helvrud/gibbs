from ion_pair_monte_carlo import MonteCarloPairs
import logging, os
import socket_nodes, getpass, time, pprint

from copy import copy, deepcopy

try: from tqdm import trange
except: trange = range

socket_nodes.set_params(LOG_REQUESTS_INFO = True)


from routines import sample_to_target, append_to_lists_in_dict

import numpy as np
import time
#logger = logging.getLogger("socket_nodes")
#logger = logging.getLogger(__name__)

try: 
    import webcolors, seaborn
    from veusz_embed import *
except ModuleNotFoundError: pass


class gel():
    start_time = time.time()
    c_s = 0.1 # mol/l
    MPC = 30
    N = MPC*16+8
    bond_length = 1.0 # used for constructing the network during the gel initialization
    A = 3*3**(0.5)/4 # The coefficient which relates volume per chain in the diamond lnetwork with the lenght of the chain R^3 = V*A


    
    lB = 2 # 0 means no electrostatic interaction. Default is 2
    alpha = 1.0

    hostname = 'skirit'
    USERNAME = 'kvint'
    HD = '/storage/brno2/home/{0}'.format(USERNAME) # home directory on skirit
    WD = HD+'/gibbs/scripts/'                                  # working directory on skirit



    eq_steps = 10000
    N_Samples = 200# number of samples,
    timeout = 60*60*24 + 60*60 # seconds (25 hours)
    #save_file_path = output_dir/output_fname

    Navogadro = 6.022e23 # 1/mol
    kT = 1.38064852e-23*300 # J
    RT = kT * Navogadro # J/mol
    # while there are no interactions sigma is arbitrary number (could be light-year), but it defines the unit of concentration

    #epsilon = 1.0 # kT
    #sigma = 1.0 # esunits
    unit_of_length = sigma_SI = 0.35 # nm
    unit = (unit_of_length*1e-9)**3*Navogadro*1000 # l/mol
    punit = kT*Navogadro/(unit/1000) # J/m3 = Pa    

    USERNAME = getpass.getuser()
    #if USERNAME == 'alexander': USERNAME = "kazakov"

    hd = '/home/{0}'.format(USERNAME)               # home directory on conteiner
    wd = hd+'/gibbs/scripts'                                  # working directory on conteiner
    pypresso = hd+'/espresso/espresso/es-build/pypresso '
    
    def __init__(self, Vbox, Vgel, Ncl):



        self.Rmax = self.MPC * self.bond_length
        self.Vmax = self.Rmax**3/self.A
        self.Vmax *= 16 
        self.Vmin =  self.MPC *16 + 8 
        self.Vbox = Vbox
        self.Vgel = Vgel
        self.Ncl = Ncl
        self.Vout = Vbox - Vgel


        self.box_l_gel = self.Vgel**(1./3)
        self.box_l_out = self.Vout**(1./3)
        
        #self.__str__()
        #arg_list_gel = ['-l', box_l_gel, '--gel' , '-MPC', self.MPC, '-bond_length', self.bond_length, '-alpha', self.alpha, '-log_name', 'test_gel.log'] + ['--no_interaction']*bool(self.lB)
        #arg_list_out = ['-l', box_l_out, '--salt', '-log_name', 'test_out.log'] + ['--no_interaction']*bool(self.lB)
        

            

    def __str__(self):

        #~ self.name = self.name+'_pCl{:.2f}'.format(self.p['Cl'])+'_lB'+str(self.lB)+'_sigma'+str(self.sigma)

        
        self.name = 'gibbs_Vgel{:.2f}_Vout{:.2f}_Ncl{}'.format(self.Vgel, self.Vout, self.Ncl)
        if self.alpha != 1.: self.name+='_alpha{:.2f}'.format(self.alpha)
        if self.lB == 0.:    self.name+='_lB{:.0f}'.format(self.lB)
        #if self.sigma == 0.: self.name+='_sigma{:.0f}'.format(self.sigma)

            
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

        print(f'Creating the qsubfile {self}.qsub') # this updates the filenames
        qsubfile = open(self.fnameqsub,'w')
        qsubfile.write('#!/bin/bash\n');
        qsubfile.write('#PBS -N '+self.name.replace('/','_')+'\n');
        #~ qsubfile.write('#$ -l nodes=1:ppn=1\n');
        #~ qsubfile.write('#$ -l walltime=200:00:00\n');
        qsubfile.write('#PBS -l mem='+mem+'\n');
        qsubfile.write('#PBS -l ncpus=3\n');
        qsubfile.write('#PBS -l walltime='+str(int(walltime))+':0:0\n');
        qsubfile.write('#PBS -m ae\n');
        qsubfile.write('#PBS -e '+self.WD+self.fnameqsuberr+'\n');
        qsubfile.write('#PBS -o '+self.WD+self.fnameqsubout+'\n');
        # ~ qsubfile.write('. /storage/praha1/home/kvint/.bashrc\n');
        #qsubfile.write('cd '+self.WD+'\n');

        #qsubfile.write('/storage/praha1/home/kvint/hydrogel/scripts/espresso/es-build/pypresso '+self.fnamepy+'\n');
        #qsubfile.write('rm /storage/brno2/home/kvint/mv/'+self.fname+'.qsubout\n')
        #qsubfile.write('rm /storage/brno2/home/kvint/mv/'+self.fname+'.qsuberr\n')
        
        qsubfile.write('singularity exec -B '+self.WD+':'+self.wd+' '+self.HD+'/ubuntu-gibbs2.img '.format(self.USERNAME) +self.pypresso+' '+self.WD+self.fname+'.py\n');
        qsubfile.close()

    def seedscript(self):
        print(f'Creating the seedscript {self}.py') # this updates the filenames
        output = []
        output.append("#!espresso/es-build/pypresso")
        # ~ output.append("#!venv/bin/python")
        output.append("import sys, os")
        output.append("os.chdir('/home/{}/gibbs/scripts')".format(self.USERNAME))
        output.append("sys.path.append('/home/{}/gibbs/scripts')".format(self.USERNAME))
        #output.append("from espressomd import reaction_ensemble")
        output.append("from gel import gel")


        output.append(f"g = gel({self.Vbox}, {self.Vgel}, {self.Ncl} )")
        output.append("g.lB = "+str(self.lB))


        # ~ output.append("g.alpha_ini = "+str(self.alpha_ini))
        output.append("g.eq_steps = "+str(self.eq_steps))
        output.append("g.timeout = "+str(self.timeout))
        output.append("g.N_Samples = "+str(self.N_Samples))
        output.append("g.run()")

        infile = open(self.fnamepy, 'w')
        for line in output:
            infile.write(line+'\n')
        infile.close()
        os.chmod(self.fnamepy, 0o774)
        
    def send2metacentrum(self):
        #self.WD = '/storage/praha1/home/kvint/mv/'
        mem = '500mb'
        walltime = int(self.timeout/60/60)
        hostname = self.hostname
        # ~ self.runfile()
        self.seedscript()
    
        self.qsubfile(walltime = walltime, mem = mem)

        # ~ os.system("scp " + self.fnamepkl  + " skirit.metacentrum.cz:"+self.WD+"data/")
        # ~ os.system("scp salt.py base.py gel.py "+hostname+".metacentrum.cz:"+self.WD)
        os.system("scp " + self.fnameqsub + " "+hostname+":"+self.WD+self.fnameqsub)
        os.system("scp " + self.fnamepy  + " " +hostname+":"+self.WD+self.fnamepy)

    def readpkl(self):
        s = 'READPKL '+ str(self) # this updates the filenames
        
        try: 
            g = pd.read_pickle(self.fnamepkl)
            print (s+' Done')
            return g
        except FileNotFoundError as e: 
            print ('\n' + s + ' FileNotFoundError\n')

        
        
    def load(self, scp = False, forcesownload = False):
        toprint = 'loadpkl '+ str(self) # this updates the filenames

        if scp:
            s = "scp "+self.hostname+":"+self.WD+self.fnamepkl +" data/"
            print (s)
            os.system(s)

        g = self.readpkl()
        if g == None: print (toprint+' return None')
        else: print (toprint+' Done')
        return g
        
    def run(self):
        tini = time.time()
        print(self) # this updates the filenames

        self.server, self.pid_gel, self.pid_out = socket_nodes.create_server_and_nodes(name = self.name, box_l_gel = self.box_l_gel, box_l_out = self.box_l_out, alpha = self.alpha, MPC = self.MPC)
        self.minimize_energy() 

        self.MC = MonteCarloPairs(self.server)
        Ncl_gel = int(self.Ncl*self.Vgel/(self.Vout+self.Vgel))
        Ncl_out = int(self.Ncl*self.Vout/(self.Vout+self.Vgel))
        Ncl_out += self.Ncl - (Ncl_gel + Ncl_out)
        self.MC.populate([Ncl_gel, Ncl_out])
        self.minimize_energy()            
        #self.equilibrate(timeout = 60+1200*(self.timeout*0.1>1200)) # equiloibrate 21 minutes (if self.timeout*0.1<1200)
        self.equilibrate(timeout = 60 + self.timeout*0.01) # equiloibrate 1 minute plus 0.01 of self.timeout (if self.timeout*0.1<1200)

        if self.lB:
            print (f'\n###    Enabling electrostatics    ###\n')
            z = self.server(f'enable_electrostatic(lB = {self.lB})', [0, 1])
            z = self.server("minimize_energy()", [0,1])
        self.equilibrate()
        self.result = self.sample()

        #self.Pearson(keys = self.keys['md']+self.keys['re'])
        self.uptime = time.time() - tini
        self.save()    
                
    def equilibrate(self, timeout = None):
        if not timeout: timeout = self.timeout*0.2
        eq_params = {'timeout_eq':timeout, 'rounds_eq':self.eq_steps, 'mc_steps_eq':500, 'md_steps_eq':10000}
        self.MC.equilibrate(**eq_params)
        
    def NN(self):
        """
        This function  returns the number of mobile anion particles in gel and in reservoir as a list
        """
        Nanion_gel  = self.server("system.number_of_particles(0)", [0])[0].result()     
        Ncation_gel = self.server("system.number_of_particles(1)", [0])[0].result()
        Nanion_out  = self.server("system.number_of_particles(0)", [1])[0].result()
        Ncation_out = self.server("system.number_of_particles(1)", [1])[0].result()

        Ngel_neutral      = self.server("system.number_of_particles(2)", [0])[0].result()          
        Ngel_anion        = self.server("system.number_of_particles(3)", [0])[0].result()
        Ngel_node_neutral = self.server("system.number_of_particles(4)", [0])[0].result()
        Ngel_node_anion   = self.server("system.number_of_particles(5)", [0])[0].result()
        print (f'Ncl_gel {Nanion_gel}\n Nna_gel{Ncation_gel}\n Ngel_neutral{Ngel_neutral}\n Ngel_anion{Ngel_anion}\n Ngel_node_neutral{Ngel_node_neutral}\n Ngel_node_anion {Ngel_node_neutral}\n Ncl_out{Nanion_out}\n Nna_out{Ncation_out}\n')
        return [Nanion_gel, Nanion_out]
   

    def save(self):
    
        import pandas as pd


        COPY = copy(self)

        try: del COPY.server
        except AttributeError: pass
        try: del COPY.MC
        except AttributeError: pass

        self.copy = deepcopy(COPY)
    
        pd.to_pickle(self.copy, self.fnamepkl)
        print(f'The object is saved to {self.fnamepkl}')
        return True

    def minimize_energy(self):
        z = self.server("minimize_energy()", [0,1])


    def sample(self, ):
        # timeout_h in hours
        target_sample_size = self.N_Samples
        timeout_s = self.timeout
        start_time = time.time()
        #add header to stored data

        #sample stored as dict of lists
        sample_d = {}
        print(f"Sampling P and N.\nTarget sample size: {target_sample_size}. Timeout: {(timeout_s/60):.1f} m")
        for i in range(target_sample_size):
            self.save()
            sampling_time = time.time()-start_time
            print (f'\nSampling {i} out of target_sample_size = {target_sample_size}')
            
            if sampling_time > timeout_s:
                print("Timeout is reached")
                sample_d['message'] = "reached_timeout"
                break
            try:
                print (f'Time spent {(sampling_time/60):.1f} m out of {timeout_s/60} m\n')
                timeout=self.timeout/target_sample_size/2 + 60
                target_eff_sample_size = 20 + self.Ncl
                particles_speciation = self.MC.sample_particle_count_to_target_error(timeout=timeout, target_eff_sample_size = target_eff_sample_size)
                print (f'Time spent {(sampling_time/60):.1f} m out of {timeout_s/60} m\n')
            except Exception as e:
                print('An error occurred during sampling while sampling number of particles')
                print(e)
                sample_d['message'] = "error_occurred"
                break
            sampling_time = time.time()-start_time
            #probably we can dry run some MD without collecting any data
            try: 
                timeout=self.timeout/target_sample_size/2 + 60
                target_eff_sample_size = 100
                pressure = self.MC.sample_pressures_to_target_error(timeout=timeout, target_eff_sample_size = target_eff_sample_size)
                print (f'Time spent {(sampling_time/60):.1f} m out of {timeout_s/60} m\n')
            except Exception as e:
                print('An error occurred during sampling while sampling pressure')
                print(e)
                sample_d['message'] = "error_occurred"
                break

            #discard info about errors
            del particles_speciation['err']
            del particles_speciation['sample_size']
            del pressure['err']
            del pressure['sample_size']
            datum_d = {**particles_speciation, **pressure}

            #to each list in result dict append datum
            append_to_lists_in_dict(sample_d, datum_d)
            self.sample_d = sample_d
            pprint.pprint(datum_d)

            #save updated data to pickle storage
            

        print(f'Sampling is done\n')
        return sample_d


if __name__ == '__main__':



    Vbox = 332553/10
    Vgel = Vbox/2
    NCl = 500
    g = gel(Vbox, Vgel, NCl)
    
    if False:    

        for Vgel in np.linspace(Vbox*0.9, Vbox, 1):
            g = gel(Vbox, Vgel, NCl)
            g.lB = 2.
            g.timeout = 24*60*60 # secounds
            #g.timeout = 60 # secounds
            
            g.N_Samples = 200
            #g.send2metacentrum()
            #g.run()
            #g.qsubfile()


    lB = 2.
    def rungel(Vgel):
        g = gel(Vbox, Vgel, Ncl)
        g.lB = lB
        #g.timeout = 23*60*60 # secounds (23 hours)
        #g.timeout = 60 # secounds
        #g.N_Samples = 100
        g.send2metacentrum()
        #g.run()
        #g.qsubfile()
        return g
        
    def loadgel(Vgel):
        g = gel(Vbox, Vgel, Ncl)
        g.lB = lB
        #g.timeout = 23*60*60 # secounds (23 hours)
        #g.timeout = 60 # secounds
        #g.N_Samples = 100
        z = g.load(scp = True)
        #g.run()
        #g.qsubfile()
        
        return z
    
    g0 = gel(Vbox, Vgel, 100)
    import pandas as pd
    GC = pd.read_pickle('../data/GC.pkl')
    Vbox_range = GC.V_eq /g.unit*g.N
    Ncl_range  = GC.Ncl_eq

    pool = False

    from multiprocessing import Pool
    GG = {}
    GB_data = pd.DataFrame(columns=['cs_gc', 'cs_gb', 'cs_gb_err', 'Ncl', 'Vbox'])
    figN = vplot()[0]
    figP = vplot()[0]
    
    n_colors = len(GC)
    colors = seaborn.color_palette("hls", n_colors)
    colors = colors.as_hex()
    
    for (index, row) in GC.iterrows():
        Vbox = row.V_eq /g0.unit*g0.N # sigma^3
        Ncl = int(np.ceil(row.Ncl_eq))
        key = f'{row.cs:0.4f} mol/l, {row.Ncl_eq:04.2f}, {Vbox:04.2f} sigma^3'
        #GB_data = GB_data.append({'cs_gc':row.cs}, ignore_index = True)
        print (key)
        Vgel_range = np.linspace(Vbox/2, Vbox, 10)

        if pool:
            pool = Pool(3)
            pool.map(rungel, Vgel_range)
            pool.close()
            pool.join()
        else: 
            #gg = list(map(rungel, Vgel_range))
            gg = list(map(loadgel, Vgel_range))
        GG[key] = gg


        plot = True
        if plot:
            CS     = np.array([])
            CS_err = np.array([])
            VGEL   = np.array([])
            P      = np.array([])
            P_err  = np.array([])
            for g in gg:
                try:
                    ncl = np.array(g.sample_d['anion'])
                    nclgel = ncl[:,0]
                    nclout = ncl[:,1]
                    nclout_mean = np.mean( nclout )
                    nclout_err  = np.std( nclout )/ (len(nclout)-1)**0.5
                    cs = nclout_mean / g.Vout / g.unit
                    cs_err = nclout_err / g.Vout / g.unit
                    pall = np.array(g.sample_d['pressure'])
                    pgel = pall[:,0]
                    pout = pall[:,1]
                    p = pgel - pout
                    p_err = np.std( p )/ (len(p)-1)**0.5
                    CS = np.append(CS, cs)
                    CS_err = np.append(CS_err, cs_err)
                    VGEL   = np.append(VGEL, g.Vgel)
                    P      = np.append(P, p)
                    P_err  = np.append(P_err, p_err)
                except AttributeError: pass             
            
            GB_data_dic = {'cs_gc':row.cs, 'Vgel':VGEL, 'cs_gb':CS, 'cs_gb_err':CS_err, 'p_gb':P, 'p_gb_err':P_err, 'Ncl':row.Ncl_eq, 'Vbox':Vbox}
            GB_data = GB_data.append(GB_data_dic, ignore_index = True)
        
        
            
            (figN, graphN, xy) = vplot([Vbox*g0.unit/g0.N],[row.cs], xname = 'vbox_gc'+str(index), yname = 'cs_gc'+str(index), markersize = '4pt', color = colors[index], g = figN)  
            
            x = GB_data.Vgel[index]*g0.unit/g0.N
            y = GB_data.cs_gb[index]
            (figN, graphN, xy) = vplot(x, y, xname = 'vbox_gb'+str(index), yname = 'cs_gb'+str(index), color = colors[index], g = figN)  
            graphN.x.label.val = 'V_{box}, l/mol'
            graphN.y.label.val = 'c_{s}'
            #graph.y.max.val = 0.5
            graphN.y.log.val = True
            graphN.x.log.val = True

            y = GB_data.p_gb[index]*g0.punit/1e5
            (figP, graphP, xy) = vplot(x, y, xname = 'vbox_gb'+str(index), yname = 'p_gb'+str(index), color = colors[index], g = figP)  
            graphP.x.label.val = 'V_{box}, l/mol'
            graphP.y.label.val = 'P^{gel'
            graphP.y.max.val = 5.1
            graphP.y.min.val = -1
            graphP.x.log.val = True
            
            
            








