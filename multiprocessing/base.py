###################################################
#  The most simple setup of Reaction  Ensemble
###################################################
import subprocess, espressomd, os, getpass, time, pprint

from espressomd import electrostatics

#~ import pickle
#~ import cPickle
import pickle as cPickle
from copy import copy, deepcopy
from espressomd import checkpointing
import scipy.linalg as la
# Functions
#~ exec(open("functions.py").read())
from functions import *
# Utils
#from utils import check_add_dir_init, check_file_exist, Capturing
try:
    import veusz.embed as veusz
except ImportError:
    pass


pprint = pprint.PrettyPrinter(indent=4).pprint

#~ if ('REACTION_ENSEMBLE' not in espressomd.code_info.features()):
        #~ print("REACTION_ENSEMBLE not compiled in.")
        #~ sys.exit()


class base():
    classname = 'base'
    #USERNAME = "kvint"

    USERNAME = getpass.getuser()
    if USERNAME == 'alexander': USERNAME = "kazakov"

    HD = '/storage/brno2/home/{0}'.format(USERNAME) # home directory on skirit
    hd = '/home/{0}'.format(USERNAME)               # home directory on conteiner
    wd = hd+'/mv/'                                  # working directory on conteiner
    WD = HD+'/mv/'                                  # working directory on skirit

    pypresso = hd+'/espresso/espresso/es-build/pypresso '
    def __init__(self):
        self.time_step = 0.005
        self.samples = {}


        # Avogadro number
        self.Navogadro = 6.022e23 # 1/mol
        self.kT = 1.38064852e-23*300 # J
        self.RT = self.kT * self.Navogadro # J/mol
        # while there are no interactions sigma is arbitrary number (could be light-year), but it defines the unit of concentration

        self.epsilon = 1.0 # kT

        self.sigma = 1.0 # esunits
        self.unit_of_length = self.sigma_SI = 0.35 # nm

        self.unit = (self.unit_of_length*1e-9)**3*self.Navogadro*1000 # l/mol

        self.punit = self.kT*self.Navogadro/(self.unit/1000) # J/m3 = Pa

        self.tini = time.time()
        self.LJ_generic = False

        self.eq_steps = 10000 # The number of equilibration steps
        self.N_Samples = 100 # The number of samples



    def __str__(self):

        #~ self.name = self.name+'_pCl{:.2f}'.format(self.p['Cl'])+'_lB'+str(self.lB)+'_sigma'+str(self.sigma)

        self.name = self.classname


        # This generates the suffixes by the dictionary self.p
        for I in ['K', 'H', 'Cl', 'Ca', 'SO4' ]:
            if I in self.p.keys():
                if self.p[I]!= np.infty:
                    self.name += '_p'+I+'{:.2f}'.format(self.p[I])



        if self.lB != 2.0:
            self.name += '_lB'+str(self.lB)
        if self.sigma != 1.0:
            self.name += '_sigma'+str(self.sigma)
        if self.epsilon != 1.0:
            self.name = self.name+'_epsilon'+str(self.epsilon)
        # ~ try:
            # ~ if self.exclusion_radius != 1.0:
                # ~ self.name = self.name+'_exclusion_radius'+str(self.exclusion_radius)
        # ~ except AttributeError:
            # ~ pass


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

    def set_EL(self,prefactor=1.0):
        if self.lB:
            print('\n #### Seting the Electrostatics ####')
            Q = self.system.part[:].q

            tini = time.time();
            if Q.any():

                # This is commented out becauses cstringio is only available in pytyon 2
                #~ with Capturing() as output:

                self.p3m = espressomd.electrostatics.P3M(prefactor=self.lB, accuracy=1e-4)
                self.system.actors.add(self.p3m)
                self.p3m.tune(accuracy=1e-4)
                self.p3m_params = self.p3m.get_params()
                print("Output of p3m captured.")
                uptime = time.time() - tini
                print('Done, uptime = ', uptime)
            else:
                print('No charges --- no P3M, uptime = ')

    def set_LJ(self):
        # Interaction parameters (repulsive Lennard Jones)
        #############################################################

        if self.sigma:
            if self.LJ_generic:
                self.set_LJ_generic()
            else:
                lj_eps = self.epsilon
                lj_sig = self.sigma
                #~ lj_cut = 1.12246
                lj_cut = self.sigma*2**(1./6)
                #~ lj_cut = self.sigma_es+1

                particles = P = list(self.TYPES.keys())
                pairs = [(P[i], P[j]) for i in range(len(P)) for j in range(i, len(P))]
                #~ print(particles, pairs)
                self.LJ_params = {}
                for pair in pairs:
                    ids = [self.TYPES[pair[0]], self.TYPES[pair[1]]]
                    self.system.non_bonded_inter[ids[0], ids[1]].lennard_jones.set_params(epsilon = lj_eps, sigma=lj_sig, cutoff=lj_cut, shift="auto")
                    self.LJ_params[pair] = self.system.non_bonded_inter[ids[0], ids[1]].lennard_jones.get_params()
                    # print(self.system.non_bonded_inter[ids[0], ids[1]].lennard_jones.get_params())
        #self.warmUp()


    def set_LJ_generic(self):

        #~ LJ_generic available parameters
            #~ {
                #~ "epsilon": ia_params.LJGEN_eps,
                #~ "sigma": ia_params.LJGEN_sig,
                #~ "cutoff": ia_params.LJGEN_cut,
                #~ "shift": ia_params.LJGEN_shift,
                #~ "offset": ia_params.LJGEN_offset,
                #~ "e1": ia_params.LJGEN_a1,
                #~ "e2": ia_params.LJGEN_a2,
                #~ "b1": ia_params.LJGEN_b1,
                #~ "b2": ia_params.LJGEN_b2,
                #~ "lam": ia_params.LJGEN_lambda,
                #~ "delta": ia_params.LJGEN_softrad
            #~ }
        # Interaction parameters (repulsive Lennard Jones)
        #############################################################
        if self.sigma:
                particles = P = list(self.TYPES.keys())
                pairs = [(P[i], P[j]) for i in range(len(P)) for j in range(i, len(P))]
                #~ print(particles, pairs)
                self.LJ_params = {}
                for pair in pairs:
                    ids = [self.TYPES[pair[0]], self.TYPES[pair[1]]]
                    self.system.non_bonded_inter[ids[0], ids[1]].generic_lennard_jones.set_params(
                        epsilon = 1.0,
                        sigma = self.sigma, #r_o = 0.5 * self.sigma
                        e1 = 2.,
                        e2 = 1.,
                        b1 = 1.,
                        b2 = 2.,
                        cutoff = self.sigma,
                        shift=1.,
                        offset = 0.)

                    self.LJ_params[pair] = self.system.non_bonded_inter[ids[0], ids[1]].generic_lennard_jones.get_params()
                    # print(self.system.non_bonded_inter[ids[0], ids[1]].lennard_jones.get_params())



    def tune_skin(self):
        print('tuning the skin')
        skin = self.system.cell_system.tune_skin(min_skin=0.1, max_skin=0.8, tol=1e-7, int_steps=100)
        self.system.cell_system.skin = skin;
        print('skin tuning done')

    def minimize_energy(self):
        try:
            from espressomd import minimize_energy
            minimize_energy.steepest_descent(self.system, f_max = 0, gamma = 10, max_steps = 2000, max_displacement= 0.01)
        except AttributeError:
            self.system.minimize_energy.init(f_max = 10, gamma = 10, max_steps = 2000, max_displacement= 0.1)
            self.system.minimize_energy.minimize()


        energies = self.system.analysis.energy()
        try:
            print('total = ', energies['total'], 'kinetic=', energies['kinetic'], 'coulomb=', energies['coulomb'])
        except KeyError:
            print('total = ', energies['total'], 'kinetic=', energies['kinetic'])

    def set_thermostat(self):
        if not hasattr(self, 'seed'):
            self.seed = int(time.time())
        self.system.thermostat.set_langevin(kT=1.0, gamma=1.0, seed = self.seed)
        self.thermostat_params = self.system.thermostat.get_state()

    def warmUp(self):
        timeini = time.time()
        print('\n #### Warming Up ####')
        # set LJ cap

        lj_cap = 1

        #self.system.minimize_energy.minimize()

        self.system.force_cap = lj_cap
        #~ self.system.thermostat.set_langevin(kT=1.0, gamma=1.0)


        if self.sigma:
            # warmup integration (with capped LJ potential)
            warm_steps = 100
            warm_n_times = 300
            # do the warmup until the particles have at least the distance min__dist
            min_dist = 0.95
            # Warmup Integration Loop
            i = 0
            act_min_dist = self.system.analysis.min_dist()
            while (i < warm_n_times and act_min_dist < min_dist):
                #~ while (act_min_dist < min_dist):

                self.system.integrator.run(steps=warm_steps)

                #~ # Warmup criterion
                act_min_dist = self.system.analysis.min_dist()
                i += 1
                lj_cap += 0.25
                self.system.force_cap = lj_cap
                print('lj_cap = ', lj_cap, 'mindist=', act_min_dist)

            # remove force capping
            lj_cap = 0
            self.system.force_cap = lj_cap
            #~ print(self.system.non_bonded_inter[0, 0].lennard_jones)
            energies = self.system.analysis.energy()
            try:
                print('total = ', energies['total'], 'kinetic=', energies['kinetic'], 'coulomb=', energies['coulomb'])
            except KeyError:
                print('total = ', energies['total'], 'kinetic=', energies['kinetic'])
            print('warmup done')
            self.tune_skin()
            uptime = time.time() - timeini  # seconds
            #~ self.uptime = self.uptime / 60. # minutes
            #~ self.uptime = round(self.uptime, 2)

            print('Done, uptime =', uptime, ' seconds')

    def integrate(self):
        # ~ print ('integration')
        self.system.integrator.run(steps=self.steps['md'])
    def reaction(self):
        #~ print ('reactionre')
        self.RE.reaction(reaction_steps = self.steps['re'])

    def getN(self, keys = []):
        # ~ if keys == []: keys = self.keys['re']
        if keys == []: keys = self.TYPES.keys()

        for key in keys:
            self.N[key] = self.system.number_of_particles(self.TYPES[key])
            try:                self.samples[key] = np.append(self.samples[key], self.N[key])
            except KeyError:    self.samples[key] = np.array([self.N[key]])
        return self.N



    def send2zeolite(self, q = '', run = True):
        #~ self.save()
        self.runfile()
        # this part prepares the scripts for qsub
        qsubfile = open(self.fnameqsub,'w')
        qsubfile.write('#!/bin/bash\n');
        qsubfile.write('#$ -N '+self.name+'\n');
        #~ qsubfile.write('#$ -l nodes=1:ppn=1\n');
        #~ qsubfile.write('#$ -l walltime=200:00:00\n');
        qsubfile.write('#$ -l mem=200\n');
        qsubfile.write('#$ -m e\n');
        if q: qsubfile.write('#$ -q '+q+' \n');
        qsubfile.write('#$ -e '+self.fnameqsuberr+'\n');
        qsubfile.write('#$ -o '+self.fnameqsubout+'\n');
        qsubfile.write('#$ -cwd\n');
        qsubfile.write('. /home/kvint/.bashrc\n');
        #~ qsubfile.write('cd $PBS_O_WORKDIR\n');
        #~ qsubfile.write('rm -f '+self.fnameout+'\n');
        qsubfile.write('source env.rc\n');
        qsubfile.write('echo $(which python) env.rc\n');

        qsubfile.write('/home/kvint/weak_periodic_gels/scripts/Oleg/espresso/es-build/pypresso '+self.fnamerun+' > '+self.fnameout+' 2>&1\n');
        qsubfile.close()

        # ~ os.system("scp functions.py salt.py acid.py base.py gel.py"+" zeolite.natur.cuni.cz:hydrogel/")


        os.system("scp "+self.fnamepkl+" zeolite.natur.cuni.cz:weak_periodic_gels/scripts/Oleg/data")
        os.system("scp "+self.fnameqsub+" zeolite.natur.cuni.cz:weak_periodic_gels/scripts/Oleg/data")
        os.system("scp "+self.fnamerun+" zeolite.natur.cuni.cz:weak_periodic_gels/scripts/Oleg/data")
        if run:
            c = os.popen("ssh zeolite.natur.cuni.cz 'source /etc/profile;  cd ~/weak_periodic_gels/scripts/Oleg/; git pull; pwd; qsub "+self.fnameqsub+"; pwd '")
            print(self.name+' submitted')

    def qsubfile(self, mem = '2gb', walltime = 24):
        # ~ self.WD = '/storage/praha1/home/kvint/hydrogel/scripts/'
        # this part prepares the scripts for qsub to run ot tarkil    WD = '/storage/brno2/home/{}/mv/'.format(USERNAME)
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
        qsubfile.write('singularity exec -B '+self.HD+':'+self.hd+' '+self.HD+'/ubuntu.img '.format(self.USERNAME) +self.pypresso+' '+self.wd+self.fname+'.py\n');
        qsubfile.close()


    def send2metacentrum(self, run = False, walltime = 2, mem = '100mb', hostname = 'skirit'):
        #self.WD = '/storage/praha1/home/kvint/mv/'

        # ~ self.runfile()
        self.seedscript()
        self.qsubfile(walltime = walltime, mem = mem)

        # ~ os.system("scp " + self.fnamepkl  + " skirit.metacentrum.cz:"+self.WD+"data/")
        # ~ os.system("scp salt.py base.py gel.py "+hostname+".metacentrum.cz:"+self.WD)
        os.system("scp " + self.fnameqsub + " "+hostname+":"+self.WD+self.fnameqsub)
        os.system("scp " + self.fnamepy  + " " +hostname+":"+self.WD+self.fnamepy)
        if run:
            print('sending the job '+ self.name+ ' to ' +hostname)
            command1 = "ssh "+hostname+" 'qsub "+self.WD+self.fnameqsub+"'"
            command2 = "ssh "+hostname+" 'rm "+self.WD+self.fnameqsub+"out'"
            command3 = "ssh "+hostname+" 'rm "+self.WD+self.fnameqsub+"err'"
            print (command1)
            print (command2)
            print (command3)

            c = os.popen(command1).read()
            c = os.popen(command2).read()
            c = os.popen(command3).read()

            # ~ print(c)
            print(self.name+' submitted')
            print()



    def pearson(self, keys):
        erros = {}
        means = {}
        corrs = {} # tau correlation time
        taus = {} # tau correlation time

        # generates a dictionary containing the carrelation coefficients of interest. Set keys variable
        for key in keys:
            X = self.samples[key]
            corrs[key] = autopearson(X, len(X)//2)
            erros[key] =  np.std(self.samples[key])
            means[key] =  np.mean(self.samples[key])
            try:
                self.Samples[key] = np.vstack((self.Samples[key], np.array([means[key], erros[key], corrs[key]])))
            except KeyError:
                self.Samples[key] = np.array([means[key], erros[key], corrs[key]])

        try:
            self.erros.update(erros)
            self.corrs.update(corrs)
            self.means.update(means)
        except AttributeError:
            self.erros = erros
            self.corrs = corrs
            self.means = means
    
    def Pearson(self, keys):
        # ~ def corr(X):
            # ~ N = len (X)
            # ~ X0 = X
            # ~ X1 = np.concatenate((X[N>>1:], X[:N>>1]))
            # ~ try:
                # ~ K = abs(pearson(X0, X1))
            # ~ except ValueError:
                # ~ K = 1.0
                # ~ #~ print '############', K
            # ~ return K

        Erros = {}
        Means = {}
        Corrs = {} # tau correlation time
        Taus =  {}

        # generates a dictionary containing the carrelation coefficients of interest. Set keys variable

        for key in keys:
            try:
                Corrs[key] = autocorrelation(self.Samples[key][:,0])
                Taus[key] = Corrs[key][1]
                Erros[key] =  np.std(self.Samples[key][:,0])/(len(self.Samples[key])-1)**0.5
                Means[key] =  np.mean(self.Samples[key][:,0])
            except (IndexError, KeyError):
                Corrs[key] = np.nan
                Taus[key] = np.nan
                Erros[key] = np.nan
                Means[key] =  np.nan
        try:
            self.Erros.update(Erros)
            self.Corrs.update(Corrs)
            self.Means.update(Means)
        except AttributeError:
            self.Erros = Erros
            self.Corrs = Corrs
            self.Means = Means

    #~ def uptime(self, function, *args, **kwargs):
        #~ tini = time.time();
        #~ function(*args, **kwargs)
        #~ uptime = time.time() - tini ;
        #~ print(function.__name__, 'done, uptime = ', uptime)
        #~ exec('self.uptime_'+function.__name__+' = uptime')


    def save(self, suffix= ''):

        #~ self.checkpoint = checkpointing.Checkpoint(checkpoint_id="mycheckpoint")
        #~ system = self.system
        #~ self.checkpoint.register("system")

        try:


            self.part = {
                'pos': self.system.part[:].pos,
                'id': self.system.part[:].id,
                'type': self.system.part[:].type,
                'bonds': self.system.part[:].bonds,
            }

            bonds = []
            BONDS = self.part['bonds']
            for i in range(len(BONDS)):
                bonds.append([i])
                for bond in BONDS[i]:
                     bonds[-1].append(bond[1])
                self.part['bonds'] = bonds

        except AttributeError: pass
        COPY = copy(self)

        try: del COPY.system
        except AttributeError: pass
        try: del COPY.RE
        except AttributeError: pass
        try: del COPY.WI
        except AttributeError: pass
        try: del COPY.p3m
        except AttributeError: pass
        try: del COPY.bond
        except AttributeError: pass
        try: del COPY.copy
        except AttributeError: pass
        try: del COPY.update_md_samples
        except AttributeError: pass


        self.copy = deepcopy(COPY)
        str(self)
        WD = os.getcwd()
        self.fnamepkl = self.fname+'_'*bool(suffix)+suffix+'.pkl'

        output = open(WD +'/'+ self.fnamepkl, 'wb')
        cPickle.dump(self.copy, output, protocol=2)
        #~ pickle.dump(dic, output)
        output.close()
        print('output saved in ', WD +'/'+ self.fnamepkl)

    def load(self, suffix= '', scp = False, USERNAME = ''):
        str(self)
        self.fnamepkl = self.fname+bool(suffix)*'_'+suffix+'.pkl'
        WD = self.WD

        if USERNAME:
            WD = self.WD.replace(self.USERNAME, USERNAME)


        if scp:
            print('download form skirit', WD+self.fnamepkl)
            # ~ os.system("scp zeolite.natur.cuni.cz:weak_periodic_gels/scripts/Oleg/"+self.fnamepkl+" data/")
            #os.system("scp tarkil.metacentrum.cz:/storage/praha1/home/kvint/mv/"+self.fnamepkl+" data/")
            os.system("scp skirit:"+WD+self.fnamepkl +' '+ os.path.dirname(self.fnamepkl)+"/")
        WD = os.getcwd()
        pkl_file = open(WD+'/'+self.fnamepkl, 'rb')
        load = cPickle.load(pkl_file)
        #~ load = cPickle.load(pkl_file, encoding='latin1')
        pkl_file.close()

        self.copy = load

        return load

    def load_merge(self, suffix= '', scp = False, ):
        #USERNAMES = ['kvint', 'kazakov', 'prokacheva']
        #USERNAMES = ['kvint', 'kazakov']
        USERNAMES = [ 'kvint']
        str(self)
        Load = []

        Samples = {}

        keys = ['Re00', 'Re01', 'Re02', 'Re03', 'Re04', 'Re05', 'Re06', 'Re07', 'Re08', 'Re09', 'Re10', 'Re11', 'Re12', 'Re13', 'Re14', 'Re15',
            'time', 'pressure', 'Na', 'Cl', 'Ca', 'PA', 'mindist', 'coords']
        for key in keys:
            Samples[key] = np.array([])

        self.fnameqsubout = self.fnamepkl.replace('.pkl', '.qsubout')
        wd = os.getcwd()
        for user in USERNAMES:
            #self.fnamepkl = self.fnamepkl.replace('data/', 'data/'+user+'/')
            WD = self.WD.replace(self.USERNAME, user)
            if scp:
                print('download from skirit', WD+self.fnamepkl)
                os.system("scp skirit:"+WD+self.fnamepkl +' '+ os.path.dirname(self.fnamepkl)+"/"+user+"/")
                os.system("scp skirit:"+WD+self.fnameqsubout +' '+ os.path.dirname(self.fnamepkl)+"/"+user+"/")
            try:
                pkl_file = open(wd+'/'+self.fnamepkl.replace('data/', 'data/'+user+'/'), 'rb')
                load = cPickle.load(pkl_file)
                #n_samples = len(load.Samples['pressure'])
                #for key in ['pressure', 'Ca', 'Na', 'Cl']:
                    #load.Samples[key] = load.Samples[key][int(n_samples*0.):] 
                
                pkl_file.close()
            except FileNotFoundError:
                load = self
                load.Samples = {}

            if load.Samples == {} or (not ('pressure' in load.Samples.keys())) or (not ('Na' in load.Samples.keys())):
                for key in keys:
                    load.Samples[key] = np.array([])
            Load.append(load)

            for key in load.Samples.keys():
                if key in ['time', 'coords' ]:
                    Samples[key] = np.append(Samples[key], load.Samples[key])
                else:
                    Samples[key] = np.append(Samples[key], load.Samples[key])
                    Samples[key] = Samples[key].reshape(len(Samples[key])//3, 3)

        merged_gel = Load[0]
        merged_gel.Samples = Samples
        #self.Samples = Samples
        #merged_gel.save()

        return merged_gel


    def energy(self):
        energy = self.system.analysis.energy()['total'] - self.system.analysis.energy()['kinetic']
        try:
            self.samples['energy'] = np.append(self.samples['energy'], energy)
        except KeyError:
            self.samples['energy'] = np.array([energy])
        return energy

    def mindist(self, p1='default', p2='default'):

        mindist = self.system.analysis.min_dist(p1, p2)
        try:
            self.samples['mindist'] = np.append(self.samples['mindist'], mindist)
        except KeyError:
            self.samples['mindist'] = np.array([mindist])
        return mindist



    def time(self):

        time = self.system.time
        try:
            self.samples['time'] = np.append(self.samples['time'], time)
        except KeyError:
            self.samples['time'] = np.array([time])
        return time



    def pressure(self):

        # ~ if self.sigma:
        pressure = self.system.analysis.pressure()['total']
        # ~ else:
            # ~ types = np.unique(self.system.part[:].type)
            # ~ N = 0
            # ~ for tp in types:
                # ~ N += self.system.number_of_particles(int(tp))
            # ~ pressure = N/self.system.volume()

        try:
            self.samples['pressure'] = np.append(self.samples['pressure'], pressure)
        except KeyError:
            self.samples['pressure'] = np.array([pressure])
        return pressure


    def pressure_tensor(self):

        #pressure_tensor = self.system.analysis.pressure_tensor()['total']
        pressure_tensor = np.real(la.eig(self.system.analysis.pressure_tensor()['total'])[0])
        [pressure_tensor_x, pressure_tensor_y, pressure_tensor_z] = pressure_tensor
        try:
            self.samples['pressure_tensor_x'] = np.append(self.samples['pressure_tensor_x'], pressure_tensor_x)
            self.samples['pressure_tensor_y'] = np.append(self.samples['pressure_tensor_y'], pressure_tensor_y)
            self.samples['pressure_tensor_z'] = np.append(self.samples['pressure_tensor_z'], pressure_tensor_z)
        except KeyError:
            self.samples['pressure_tensor_x'] = np.array([pressure_tensor_x])
            self.samples['pressure_tensor_y'] = np.array([pressure_tensor_y])
            self.samples['pressure_tensor_z'] = np.array([pressure_tensor_z])
        return pressure_tensor



    def coords(self):


        self.part = {
                'pos': self.system.part[:].pos,
                'id': self.system.part[:].id,
                'type': self.system.part[:].type,
                'bonds': self.system.part[:].bonds,
            }
        bonds = []
        BONDS = self.part['bonds']
        for i in range(len(BONDS)):

                bonds.append([i])
                for bond in BONDS[i]:
                     bonds[-1].append(bond[1])
                self.part['bonds'] = bonds

        try:
                self.Samples['coords'] = np.append(self.Samples['coords'], self.part)
        except KeyError:
                self.Samples['coords'] = np.array([self.part])

        return self.part




    def odin0brun(self):
        self.__str__()

        self.save()
        self.runfile()
        outfile = open(self.fnameout,'w')
        subprocess.Popen(["python", self.fnamerun], stdout=outfile)
        outfile.close()

    def writepdb(self):
        import MDAnalysis as mda
        from espressomd import MDA_ESP

        # ... add particles here
        eos = MDA_ESP.Stream(self.system)  # create the stream
        u = mda.Universe(eos.topology, eos.trajectory)  # create the MDA universe

        # example: write a single frame to PDB
        u.atoms.write('data/'+self.name+".pdb")

        # example: save the trajectory to GROMACS format
        from MDAnalysis.coordinates.TRR import TRRWriter
        W = TRRWriter("traj.trr", n_atoms=len(self.system.part))  # open the trajectory file
        for i in range(100):
            self.system.integrator.run(1)
            u.load_new(eos.trajectory)  # load the frame to the MDA universe
            W.write_next_timestep(u.trajectory.ts)  # append it to the trajectory

    def blender(self):
        selfcopy = self.load_merge(scp = False)
        selfdict = selfcopy.__dict__
        #~ selfdict = { 'a':1, 'b':2 }
        dict_file = self.fnamepkl+'_dict'
        output = open(dict_file, 'wb')
        print('dict is saved in ', dict_file)
        cPickle.dump(selfdict, output)
        output.close()
        # subprocess.run(["blender", "-P", "blender.py", self.fnamepkl])  # doesn't capture output (py3)
        print (self.fnamepkl)
        subprocess.call(["blender", "-P", "blender.py", dict_file])  # doesn't capture output (py2)
    def xyz(self):
        xyzfile = self.fname+'.xyz'
        output = open(xyzfile, 'w')

        string = 'pbc'+3*(' '+ str(self.box_l))+'\n'
        output.write(string)
        inv_TYPES = dict()
        for key, value in self.TYPES.items():
            inv_TYPES[value] = key
        pos = self.part['pos'] % self.box_l
        types = self.part['type']
        bonds = self.part['bonds']
        for bond in bonds:
            if len(bond)>1:
                string = 'bond '+str(bond[0])+':'+str(bond[1])+'\n'
                output.write(string)
        numberofatoms = sum(types==self.TYPES['nodes'])+sum(types==self.TYPES['PA'])+sum(types==self.TYPES['PHA'])
        output.write(str(numberofatoms)+'\n\n')
        for i in  range(numberofatoms):
            TYPE = inv_TYPES[self.part['type'][i]]
            string = TYPE+' '+str(pos[i])[1:-1]+'\n'
            print (string)
            output.write(string)

        for j in  range(i, len(pos)):
            TYPE = inv_TYPES[self.part['type'][j]]
            output.write('1\n\n')
            string = TYPE+' '+str(pos[j])[1:-1]+'\n'
            print (string)
            output.write(string)
        output.close()

    def writevtf(self):


        fp = open(self.fname+'.vtf', mode='w+t')
        fp.write("unitcell {} {} {}\n".format(self.box_l,self.box_l,self.box_l))
        coords = np.random.choice(self.Samples['coords'])
        
        for i in range(len(coords['id'])):
            idx = coords['id'][i]
            typ = coords['type'][i]
            #print("atom {} radius 1 name {} type {}\n".format(idx, typ, typ))
            #radius = 0.5
            #if typ in [self.TYPES['nodes'],self.TYPES['PA'],self.TYPES['PHA']]: radius = 1
            radius = 1.0
            fp.write("atom {} radius {} name {} type {}\n".format(idx, radius, typ, typ))

        for b in coords['bonds']:
            if len(b) > 0:
                for i in b[1:]:
                    #print("bond {}:{}\n".format(b[0], i))
                    fp.write("bond {}:{}\n".format(b[0], i))

        fp.write("timestep indexed\n")
        for i in range(len(coords['id'])):
            pos = coords['pos'][i]  # % self.box_l is needed to wrap coordinates to simulation box
            idx = coords['id'][i]
            #print("{} {} {} {}\n".format(idx, pos[0], pos[1], pos[2]))
            fp.write("{} {} {} {}\n".format(idx, pos[0], pos[1], pos[2]))
        
        fp.close()
        self.fnamevtf = self.fname+'.vtf'
        #print (self.fnamevtf)
        return
    def writemol2(self):
        coords = np.random.choice(self.Samples['coords'])
        # For reference of mol2 file format see the link https://chemicbook.com/2021/02/20/mol2-file-format-explained-for-beginners-part-2.html
        strings = []

        strings.append("# Name: combgel\n")
        strings.append("@<TRIPOS>MOLECULE\n")
        strings.append(self.name.replace('/','_')+"\n")
        strings.append(str(len(coords['id']))+' '+str(len(coords['bonds'])+7)+'\n')
        strings.append("SMALL\n")
        strings.append("USER_CHARGES\n")
        strings.append("@<TRIPOS>ATOM\n")
        
        coords_pos = coords['pos'] % self.box_l
        for i in range(len(coords['id'])):
            idx = coords['id'][i]
            name = self.NAMES[coords['type'][i]][0].upper()
            coord = coords_pos[i]
            #print("atom {} radius 1 name {} type {}\n".format(idx, typ, typ))
            #radius = 0.5
            #if typ in [self.TYPES['nodes'],self.TYPES['PA'],self.TYPES['PHA']]: radius = 1
            strings.append("{} {} {:3.3f} {:3.3f} {:3.3f} {}\n".format(idx, name, coord[0], coord[1], coord[2], name))
        strings.append("@<TRIPOS>BOND\n")
        
        i = 0
        for b in coords['bonds']:
            if len(b) > 0:
                for j in b[1:]:
                    if np.linalg.norm(coords_pos[b[0]] - coords_pos[j])<2.1:
                        strings.append("{} {} {} 1\n".format(i, b[0], j))
                        i+=1
            #print(i)
        strings[3] = str(len(coords['id']))+' '+str(i)+'\n'
        fp = open(self.fname+'.mol', mode='w+t')
        for s in strings:
            fp.write(s)
        fp.close()
        self.fnamemol = self.fname+'.mol'
        print ('structure saved in '+self.fnamemol)
        return

    def VMD(self, run=False):
        self.writevtf()
        #input file
        vmd_title = open('vmd_title.tcl', "rt")
        types_text = 'set type_na {}\n'.format(self.TYPES['Na'])
        types_text += 'set type_cl {}\n'.format(self.TYPES['Cl'])
        types_text += 'set type_ca {}\n'.format(self.TYPES['Ca'])
        types_text += 'set type_pa {}\n'.format(self.TYPES['PA'])
        types_text += 'set type_pha {}\n'.format(self.TYPES['PHA'])
        types_text += 'set type_nodes {}\n\n'.format(self.TYPES['nodes'])
        
        
        vmd_title_txt = vmd_title.read()
        vmd_title.close()
        vmd_title_txt = types_text + vmd_title_txt.replace("Put a name of VFT file here", self.fnamevtf)
        vmd_title_txt += 'scale to 0.05\n'
        vmd_title_txt += 'render snapshot '+self.fname+'.tga\n'
        self.fnamevmd = self.fname+'.vmd'
        #output file to write the result to
        fout = open(self.fnamevmd, "wt")
        fout.write(vmd_title_txt)
        fout.close()
        print ('VMD vile saved: '+self.fnamevmd)
        if run:
            os.popen('vmd -e '+self.fnamevmd)
        else: 
            # this commands would render the vmd file            
            os.popen('echo exit >> '+self.fnamevmd)
            os.popen('vmd -dispdev text -e '+self.filename.vmd)
            os.popen('convert '+self.filename+'.tga '+self.filename+'.jpg')
            
        return        
        
        
   

def plotLJ(sigma = 1):
        r = np.linspace(0,10)

        epsilon = 1.0,
        sigma=sigma, #r_o = 0.5 * sigma
        e1 = 2.,
        e2 = 1.,
        b1 = 1.,
        b2 = 2.,
        cutoff=sigma,
        shift=1.,
        offset = 0.

        Y = epsilon*(b1*(sigma/(r-offset))**e1 - b2*(sigma/(r-offset))**e2 + shift)
        vplot(r,Y, xname = 'r_sigma'+str(sigma), yname = 'LJ_sigma'+str(sigma))
