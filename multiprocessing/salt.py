###################################################
#  The most simple setup of Reaction  Ensemble    #
###################################################
#~ import subprocess
import espressomd
import socket
from espressomd import reaction_ensemble
from espressomd import code_info
from espressomd import interactions
from copy import copy, deepcopy
import pprint
#~ import random
import os, sys, time, random
import numpy as np
try:
    import veusz.embed as veusz
except ImportError:
    pass

import pprint
pprint = pprint.PrettyPrinter(indent = 4).pprint

try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError

#exec(open("functions.py").read())
from functions import *
from base import base
class salt(base):
    classname = 'salt'
    N_Samples = 200
    eq_steps = 10000
    corr_criterion = 1/np.e
    widom=False
    def __init__(self):
        self.name = 'salt'
        #~ self.box_l = box_l
        #~ self.volume = box_l**3
        base.__init__(self)
        # Parameters section


        self.val = {
            'Cl':  -1,
            'OH':  -1,
            'Br':  -1,
            'Na':  +1,
            'H' :  +1,
            'K' :  +1,
            'Ca':  +2,
            'SO4': -2,
            }
        self.p = {
            'Na': 3.,
            'H' : 7.,
            }

        Kw = 1e-14 # (mol/l)**2
        pKw = -np.log10(Kw)
        self.p['OH'] = pKw - self.p['H']
        self.p['Cl'] = self.p['Na']
        if 'Ca' in self.p.keys():
            self.p['Br'] = -np.log10(2*10**-self.p['Ca'])
        if 'SO4' in self.p.keys():
            self.p['K'] = -np.log10(2*10**-self.p['SO4'])


        self.mu = {}
        for key in self.p.keys():
            self.mu[key] = -np.log(10**(-self.p[key])*self.unit)


        self.sigma = 1.0 # [ sigma ]
        self.lB = 2.0 # Bjerrum length in water [ sigma ]


        try: idx = max(self.TYPES.values())+1
        except AttributeError: idx = 0; self.TYPES = {}

        type_names = ['Cl', 'Na', 'H', 'OH', 'Ca', 'SO4']
        for type_name in type_names:
            self.TYPES[type_name] = idx; idx+=1

        self.NAMES = {} # the inverse to TYPES dictionary
        for key in self.TYPES.keys():
            val = self.TYPES[key]
            self.NAMES[val] = key

        # a minimum number of particles present in box needed for blowing up
        # this number is small because the concentration of divalent ions is supposed to be smaller than of the monovalent ones,
        # So the function blowup will increase the box untill we have Nmin of SO4 ions
        self.Nmin = 64


        self.Samples = {}


        self.keys = {} # This is the dictionary for the key values of interest
        self.keys['md'] = ['pressure']
        self.keys['re'] = []
        


        self.steps = {} # The dictionary storing number of steps for each process ie fhen calling integrate, reaction
        self.steps['md'] = 256
        self.steps['re'] = 64

        self.n_samples = {}
        self.n_samples['re'] = 100 # number of samples in one reaction run step
        self.n_samples['md'] = 50 # number of samples in one md step
 
        self.exclusion_radius = 1.0*self.sigma

    def setup_pair_insertion(self, cation = 'Na', anion = 'Cl', widom = False):
        print( 'Setting up '+cation+' and '+anion+' pair insertion')
        type_cation  = self.TYPES[cation]
        type_anion   = self.TYPES[anion]

        nu_cation = abs(self.val[anion])
        nu_anion  = abs(self.val[cation])


        CHARGES = {}
        CHARGES[type_cation] = self.val[cation]
        CHARGES[type_anion]  = self.val[anion]


        if widom:
            self.WI.add_reaction(
                    reactant_types=[],
                    reactant_coefficients=[],
                    product_types=[type_cation,type_anion],
                    product_coefficients=[nu_cation, nu_anion],
                    default_charges=CHARGES)
        else:
            gamma = np.exp( -self.mu[cation]*nu_cation - self.mu[anion]*nu_anion )

            exec('self.K_'+cation+anion+' = gamma')
            print ('self.K_'+cation+anion+' = ', gamma)            
            for i in range(nu_cation):
                pos=np.random.random(3) * self.box_l
                self.system.part.add(pos=pos, type=type_cation, q=self.val[cation])
            for i in range(nu_anion):
                pos=np.random.random(3) * self.box_l
                self.system.part.add(pos=pos, type=type_anion, q=self.val[anion])            
                
            self.RE.add_reaction(gamma=gamma,
                        reactant_types=[],
                        reactant_coefficients=[],
                        product_types=[type_cation,type_anion],
                        product_coefficients=[nu_cation, nu_anion],
                        default_charges=CHARGES)

    def set_insertions(self):
        # This will run only if self.p['Cl'] is set
       
        if self.p['Cl'] != np.infty:
            self.keys['re'] += ['Na', 'Cl']
            if self.p['Ca'] != np.infty: self.keys['re'] += ['Ca']
            
            types = []
            type_ids = []
            self.mu = {} # update mus first
            print ('\n Setting Up reactions... part_types = ', self.keys['re'])

            for key in self.keys['re'][1:]:
                self.mu[key] = -np.log(10**(-self.p[key])*self.unit)
                types += [key]
                type_ids += [self.TYPES[key]]
                
            self.RE = reaction_ensemble.ReactionEnsemble(temperature=1., seed = np.random.rand(), exclusion_radius=self.exclusion_radius)
            self.system.setup_type_map(type_ids)
            pairs = []
            for i in range(len(types)):
                for j in range(i, len(types)):
                    if types[i] != types[j]:
                        if self.val[types[i]]*self.val[types[j]] < 0:
                            pairs.append((types[i], types[j]))

            for pair in pairs:
                self.setup_pair_insertion(cation = pair[0], anion = pair[1])

            self.RE_params = self.RE.get_status()
            self.RE_params['volume'] = self.RE.get_volume()      



    def blowup(self):
        self.equilibrate(eq_steps=int(self.eq_steps/2))
        N = min(self.N.values()) + 1
        print (N)
        while N < self.Nmin:
            N = min(self.N.values())+1 # plus 1 guarantees that N is not zero
            self.box_l *= (1.+2./N)**(1./3) # 2. means to increase volume such that 10 more particle will fit in new volume
            #~ print ('box_l = ', self.box_l, N)
            self.system.box_l = [self.box_l] * 3
            self.volume = self.box_l**3
            self.RE.set_volume(self.volume)
            # ~ self.RE.set_volume(self.volume)
            self.RE_params['volume'] = self.RE.get_volume()
            self.__str__()
            self.equilibrate(eq_steps=int(self.eq_steps/2))
            print ('N = ', self.N, 'box_l = ', self.box_l)


    def update_re_samples(self):
        return self.getN(keys = self.keys['re'])
        
    def update_md_samples(self):
        ''' returns either mindist or pressure(if sigma is not zero)'''
        fl = (not self.sigma)*[self.mindist]+bool(self.sigma)*[self.pressure]
        return [f() for f in fl]

    def equilibrate(self, eq_steps = 0):

        # Equillibration
        tini = time.time()
        box_l = self.box_l
        if not eq_steps:
            eq_steps = self.eq_steps
        print( '\n #### Equillibration ####, eq_steps = ', eq_steps )

        self.N = {}

        stage = 0

        choices = [self.integrate]
        keysmd = self.keys['md']
        keys=keysmd
        keysre = []
        

        if hasattr(self, 'RE'):
            choices += [self.reaction]
            keysre += self.keys['re']
            keys = keysre + keysmd


        for key in keys: self.samples[key] = np.array([])
        for i in range(eq_steps):
            np.random.choice(choices)()
            stage += 1.
            self.update_md_samples()
            if abs(self.p['Na']) != np.inf or abs(self.p['K']) != np.inf:
                #if 'mindist' in keysre: keysre.remove('mindist')
                N = self.getN(keys = keysre)
                print(round(stage/eq_steps*100), '% N=', self.N)
            # ~ print (self.samples[keysmd[0]][-1])
            self.pearson(keys)
            print ('Means')
            pprint(self.means)
        print ('Means')
        pprint(self.means)
        print ('Erros')
        pprint(self.erros)
        print ('Corrs')
        pprint(self.corrs)
        self.Samples={}
        self.Samples['time'] = np.array([])
        uptime = time.time() - tini
        print('Done, uptime = ', round(uptime,2), ' sec\n')


    def addPair(self):
        pos = self.system.box_l*np.random.rand(3)
        v_av = (2*self.system.analysis.energy()['kinetic'])**0.5
        v = np.zeros(3)
        v[np.random.randint(3)] = v_av
        a = self.system.part.add(pos=pos, type=self.TYPES['Na'], q=+1., v=v)
        v[np.random.randint(3)] = -v_av
        b =self.system.part.add(pos=pos, type=self.TYPES['Cl'], q=+1., v=v)
        return [a,b]

    def removePair(self):
        ids = self.system.part[:].id
        #finds ids of array elements where type is Na )these ids are not the particle ids!!!)
        whereNa = self.system.part[:].type == self.TYPES['Na']
        whereCl = self.system.part[:].type == self.TYPES['Cl']

        Naids = ids[whereNa]
        Clids = ids[whereCl]

        Naid  = np.random.choice(Naids)
        Clid  = np.random.choice(Clids)
        
        a = self.system.part[Naid]
        b = self.system.part[Clid]
        abak = [a.id, a.pos, a.v, a.type, a.q]
        bbak = [b.id, b.pos, b.v, b.type, b.q]

        self.system.part[Naid].remove()
        self.system.part[Clid].remove()
        
        return [abak, bbak]
        

    def sampleRE(self):
        # This will run only if self.RE initialized
        try:
            self.RE
            tini = time.time()
            print('\nsampling RE')
            n_samples = self.n_samples['re']


            corr = {}
            rekeys = self.keys['re']
            for key in rekeys:
                self.samples[key] = np.array([])

            for i in range(n_samples):
                self.reaction()
                self.update_re_samples()
                #~ print(self.samples['Na'][-1])

            for key in rekeys:
                X = self.samples[key]
                corr[key] = abs(autopearson(X, len(X)//2)) # this returns Pearson coeff of the arrya
            print ('RE correlations')
            pprint(corr)

            while (np.array(list(corr.values())) > self.corr_criterion).any():
                for i in range(n_samples):
                    self.reaction()
                    self.update_re_samples()

                for key in rekeys:
                    self.samples[key] = np.random.choice(self.samples[key],n_samples)
                    X = self.samples[key]
                    corr[key] = abs(autopearson(X, n_samples//2)) # this returns Pearson coeff of the arrya
                print ('RE correlations')
                pprint(corr)

            self.pearson(keys = rekeys)
            uptime = time.time() - tini
            print('uptime_re = ', round(uptime,2), ' sec, ')
            pprint(self.means)
        except AttributeError: pass

    def sampleMD(self):
        # gets list of functions as a parameter
        # functions are the pressure, calc_Re, energy, etc

        tini = time.time()
        print('\nsampling MD')
        n_samples = self.n_samples['md']
        mdkeys = self.keys['md']
        corr = {};
        for key in mdkeys:
            self.samples[key] = np.array([])

        for i in range(n_samples):
            self.integrate()
            self.update_md_samples()


            #~ self.mindist()
            #~ self.time()
        for key in mdkeys:
            X = self.samples[key]
            corr[key] = abs(autopearson(X, len(X)//2)) # this returns Pearson coeff of the arrya
        print ('MD correlations')
        pprint(corr)

        while  (np.array(list(corr.values())) > self.corr_criterion).any():
            #~ R = np.unique(np.array(n_samples*np.random.rand(n_samples), dtype = int))
            for i in range(n_samples):
                self.integrate()
                self.update_md_samples()

            for key in mdkeys:
                self.samples[key] = np.random.choice(self.samples[key],n_samples)
                X = self.samples[key]
                corr[key] = abs(autopearson(X, n_samples//2)) # this returns Pearson coeff of the arrya

            print ('MD correlations')
            pprint(corr)
        print ('MD correlations')
        pprint(corr)

        self.Samples['time'] = np.append(self.Samples['time'], self.system.time)
        self.pearson(keys = mdkeys)
        uptime = time.time() - tini
        #~ print('uptime_md = ', round(uptime,2), ' sec\n')
        print('uptime_md = ', round(uptime,2), ' sec, ')
        for key in mdkeys:
            print('mean ' + key + ' = ', self.means[key])



    def sample(self):
        tini = time.time()
        print( '\n #### Sampling ####' )
        choices = []
        choices = [self.sampleMD]
        # ~ if self.sigma: choices = [self.sampleMD]
        # ~ else: self.keys['md'] = []
        if hasattr(self, 'RE'  ): choices += [self.sampleRE]
        

        for i in range(self.N_Samples):
            self.sampleMD()
            self.sampleRE()
            print('{:.2f}%'.format(i/self.N_Samples*100))
            self.save()
            if i%10==0: self.coords(); print('coords are saved')

        #mdre = np.zeros(len(choices))
        #while (mdre < self.N_Samples).any():

            #~ progressBar(mdre[0], N, bar_length=20, text = self.name)
            #choice = np.random.randint(len(mdre)) #this choices between re and md steps
            #mdre[choice]+=1
            #choices[choice]()
            #print('{:.2f}%'.format(mdre[0]/self.N_Samples*100))
            #self.save()
            #if mdre[0]%10==0: self.coords(); print('coords are saved')

        uptime = time.time() - tini
        print('Done, uptime = ', round(uptime/60,2), ' min\n')

        return self.Samples


    def sample_onlyRE(self):
        tini = time.time()
        print( '\n #### Sampling ####' )


        self.Samples = {}

        re = 0
        while re < self.N_Samples:

            #~ progressBar(mdre[0], N, bar_length=20, text = self.name)

            re+=1
            self.sampleRE()
            print(round(re/self.N_Samples*100), '%')

        uptime = time.time() - tini
        print('Done, uptime = ', round(uptime/60,2), ' min\n')

        return self.Samples
    def Lucie(self):
        files = [ 'pe.pressure_output_r0_0.30', 'pe.pressure_output_r0_0.35', 'pe.pressure_output_r0_0.175']
        colors = ['green', 'red', 'blue']
        for f in range(len(files)):
            data  = open('Lucie/'+files[f]).read()

            data = data.split('\n')
            data = data[1:-1]
            for i in range(len(data)):
                data[i] = data[i].split(" ")
            data = np.array(data, dtype = float)
            data = data.T
            gamma = data[0]
            box_l = data[1]
            N = data[2]
            Nerr = data[3]
            C = N/(2.*self.Navogadro*(box_l*1e-8)**3)
            mu_ex = np.log(gamma/(self.Navogadro**2*(1e-8)**6)) - 2.*np.log(N/(2.*self.Navogadro*(box_l*1e-8)**3))
            vplot(C, mu_ex, xname = files[f]+'_C', yname = files[f]+'mu', xlog = True, color = colors[f], PlotLine = False, markersize = '3pt', marker = 'square')
            print (gamma)



    def Tobias(self):
        #files = os.listdir('tobias')
        files = [ 'mu_ex_bjer_0.5.dat', 'mu_ex_bjer_1.0.dat', 'mu_ex_bjer_2.0.dat', 'gamma_prausnitz.dat', 'exp_activity_sodium_chloride.dat']
        bjer = np.array([0.5, 1.0, 2.0])

        colors = ['black', 'green', 'red', 'blue', 'magenta']

        for f in range(len(files)):
            #~ data  = open('tobias/mu_ex_bjer_0.5.dat').read()
            data  = open('data/tobias/'+files[f]).read()

            data = data.split('\n')


            if files[f] == 'exp_activity_sodium_chloride.dat':
                data = data[1:-1]
                for i in range(len(data)):
                    data[i] = data[i].split(" ")
                data = np.array(data, dtype = float)

                colors[f] = 'black'
                CC = data[:,0]
                gamma = data[:,1]
                MuMu = 2*np.log(gamma)
                MuMu_exp_activity_sodium_chloride = MuMu
                CC_exp_activity_sodium_chloride = CC
                #~ vplot(CC, MuMu, xname = files[f]+keys[0], yname = files[f]+keys[1], xlog = True, color = colors[f], PlotLine = False, markersize = '3pt', marker = 'square')
                #~ xy.key.val = 'experiment'

            elif files[f] == 'gamma_prausnitz.dat':
                data = data[1:-1]
                for i in range(len(data)):
                    data[i] = data[i].split(" ")
                data = np.array(data, dtype = float)
                colors[f] = 'black'
                CC = data[:,0]
                gamma = data[:,1]
                MuMu = 2*np.log(gamma)
                MuMu_gamma_prausnitz = MuMu
                CC_gamma_prausnitz = CC
                print (CC_gamma_prausnitz)
                #~ vplot(CC, MuMu, xname = files[f]+keys[0], yname = files[f]+keys[1], xlog = True, color = colors[f], PlotLine = False, markersize = '3pt', marker = 'square')
                #~ xy.key.val = 'experiment'
            else:
                if files[f] == 'mu_ex_bjer_0.5.dat': colors[f] = 'green'
                if files[f] == 'mu_ex_bjer_1.0.dat': colors[f] = 'red'
                if files[f] == 'mu_ex_bjer_2.0.dat': colors[f] = 'blue'
                keys = data[0].split(' ')
                dic = {}
                for key in keys: dic[key] = []


                #~ vals = data[1:-1]
                data = data[0:-1]
                for i in range(len(data)):
                    data[i] = data[i].split(' ')
                data = np.array(data).T
                for row in data:
                    dic[row[0]] = np.array(row[1:],dtype = float)
                #keys = ['dens', 'mu_ex', 'mu_ex_err']
                sigma = bjer[f]*0.5
                unit = (0.35*1e-9)**3*self.Navogadro*1000 # l/mol
                CC = dic[keys[0]] / unit * sigma **3
                #~ MuMu = -dic[keys[1]] + np.log(dic[keys[0]])
                MuMu = dic[keys[1]]

                #~ vplot(CC, MuMu, xname = files[f]+keys[0], yname = files[f]+keys[1], xlog = True, color = colors[f], PlotLine = False, markersize = '3pt', marker = 'square')
                #~ xy.key.val = '\sigma / \lambda_{B} = '+str(1./bjer[f])
            #~ x_axis.min.val = 1e-4
            #~ y_axis.max.val = 0.5
        CC = np.append(CC_gamma_prausnitz, CC_exp_activity_sodium_chloride)
        MuMu = np.append(MuMu_gamma_prausnitz, MuMu_exp_activity_sodium_chloride)
        #~ CC = np.sort(CC)
        #~ MuMu = np.sort(MuMu)
        return CC, MuMu



    def getmu(self, cs):
        # cs in mol/l
        
        Ncl = 135
        Nna = 103
        Nca = 16
        cs_es = cs * self.unit
        V = Ncl / cs_es
        self.box_l = round(V**(1./3), 3)
        print ('box_l = ', self.box_l)
        self.system = espressomd.System(box_l = [self.box_l]*3)
        self.system.time_step = self.time_step
        self.system.cell_system.skin = 0.4
        type_ca = self.TYPES['Ca']
        type_na = self.TYPES['Na']
        type_cl = self.TYPES['Cl']
        
    
        for i in range(Nna):
            pos=np.random.random(3) * self.box_l
            self.system.part.add(pos=pos, type=type_na, q=self.val['Na'])   
        for i in range(Nca):
            pos=np.random.random(3) * self.box_l
            self.system.part.add(pos=pos, type=type_ca, q=self.val['Ca'])   
        for i in range(Ncl):
            pos=np.random.random(3) * self.box_l
            self.system.part.add(pos=pos, type=type_cl, q=self.val['Cl'])   


        
        #~ self.box_l = 10
        self.integrate()
        self.WI = reaction_ensemble.WidomInsertion  (temperature=1., seed = np.random.rand())
        self.setup_pair_insertion(cation = 'Na', anion = 'Cl', widom = True)
        self.setup_pair_insertion(cation = 'Ca', anion = 'Cl', widom = True)
        self.WI_params = self.WI.get_status()
        self.WI_params['volume'] = self.WI.get_volume()


        self.set_LJ()
        if self.lB: self.set_EL()
        
        
        num_samples = 10000
        print('measuring excess chemical potential')
        for _ in range(num_samples):
            # 0 for insertion reaction
            self.WI.measure_excess_chemical_potential(0)
            self.WI.measure_excess_chemical_potential(1)
        mu_ex0 = self.WI.measure_excess_chemical_potential(0)
        mu_ex1 = self.WI.measure_excess_chemical_potential(1)

        self.integrate()
        return (mu_ex0, mu_ex1)

    def run(self):
        tini = time.time()
        self.keys['md'] = ['pressure']
        self.update_md_samples = self.pressure
        if self.p['Ca'] != np.infty: self.Nmin = int(self.Nmin*10**(self.p['Cl'] - self.p['Ca'])+16)
        # ~ if self.sigma:
            # ~ self.keys['md'] = ['pressure']
            # ~ self.update_md_samples = self.pressure
        # ~ else:
            # ~ self.keys['md'] = ['mindist']
            # ~ self.update_md_samples = self.mindist

        self.__str__() # this updates the filenames
        print(self.fnamepkl)

        # initializing the Espresso
        # Set the box_l such that the box contains approx Nmin particles
        Ces = 10**(-self.p['Cl'])*self.unit # concentration of Cl ions in ES units
        self.box_l = max((self.Nmin/Ces)**(1./3), 5*self.sigma)
        print ('box_l = ', self.box_l)
        self.volume = self.box_l**3
        self.system = espressomd.System(box_l = [self.box_l]*3)
        #self.system.set_random_state_PRNG()

        self.system.time_step = self.time_step
        self.system.cell_system.skin = 0.4
        #~ self.box_l = 10
        self.integrate()
        # ~ self.set_insertions(part_types = ['Na', 'Cl', 'Ca'])
        self.set_insertions()
        # ~ self.set_insertions(part_types = ['Na', 'Cl', 'Ca', 'SO4'])

        # save init and blender
        # self.save()
        # self.blender()


        self.set_LJ()

        if self.lB: self.set_EL()

        self.blowup()
        self.equilibrate()
        #~ self.coords()
        #~ os.popen('blender -P sphere.py')
        #~ return

        print("\n ### RESULT ")

        #~ self.sample_onlyRE()
        self.sample()
        #~ self.plot()
        self.Pearson(keys = self.keys['re'])
        self.uptime = time.time() - tini
        self.save()
        # ~ os.popen('cp '+self.name+'.pkl '+self.name+'final.pkl ')

    def seedscript(self):
        output = []
        
        
        
        output.append("#!espresso/es-build/pypresso")
        output.append("#!espresso/es-build/pypresso")
        # ~ output.append("#!venv/bin/python")
        output.append("import sys, os")
        output.append("os.chdir('/home/{}/mv')".format(self.USERNAME))
        output.append("sys.path.append('/home/{}/mv')".format(self.USERNAME))
        output.append("from espressomd import reaction_ensemble")
        output.append("from salt import salt")
        output.append("from numpy import inf")
        
        output.append("s =salt()")
        output.append("s.lB = "+str(self.lB))
        # ~ output.append("s.exclusion_radius = "+str(self.exclusion_radius))

        if 'Cl' in self.p.keys():
            output.append("s.p['Cl'] = "+str(self.p['Cl']))
            output.append("s.p['Na'] = "+str(self.p['Na']))
        if 'H' in self.p.keys():
            output.append("s.p['H'] = "+str(self.p['H']))
            output.append("s.p['OH'] = "+str(self.p['OH']))

        if 'Ca' in self.p.keys():
            output.append("s.p['Ca'] = "+str(self.p['Ca']))

        if 'SO4' in self.p.keys():
            output.append("s.p['SO4'] = "+str(self.p['SO4']))

        output.append("s.N_Samples = "+str(self.N_Samples))
        output.append("s.sigma = "+str(self.sigma))
        output.append("s.run()")

        infile = open(self.fnamepy, 'w')
        for line in output:
            infile.write(line+'\n')
        infile.close()
        os.chmod(self.fnamepy, 0o774)

if __name__ == '__main__':
    s =salt()
    s.widom = True
    mu_ex = s.getmu(0.000015)
#    s.sigma = 1.0
    #s.lB = 2.0
    s.N_Samples = 10
    s.Nmin = 64
    #label = r'$\sigma = '+str(s.sigma)+'$, $l_{B}= '+str(s.lB)+'$'
    mu_na_id = mu_cl_id = mu_ex[0][0]    
    mu_na = mu_cl = mu_ex[0][0]
    self.mu[key] = -np.log(10**(-self.p[key])*self.unit)
    #cs = 0.15 # mol/l
    #s.p['Cl'] = -np.log10(cs)
    #s.p['Na'] = -np.log10(cs*0.873)
    #s.p['Ca'] = -np.log10(cs*0.114)
    
    #s.p['Ca'] = np.infty
    #s.p['Na'] = -np.log10(cs)
    

    
    # ~ s.p['Na'] = s.p['Cl'] = pCl
    # ~ s.p['H'] = s.p['OH'] = 7
    # ~ s.save()
    #s.eq_steps = 10
    #str(s)
    #s.run()
    # ~ s.send2metacentrum(run = True, hostname = 'tarkil')
