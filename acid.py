###################################################
#  The most simple setup of Reaction  Ensemble
###################################################
from __future__ import print_function
import espressomd
import socket
from espressomd import code_info, polymer, interactions, electrostatics, visualization, reaction_ensemble
from copy import copy, deepcopy

#~ from espressomd.io.writer import h5md

import random
import subprocess
import os, sys, time
import numpy as np
try:
    import veusz.embed as veusz
except ImportError:
    pass

try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError



import pprint
pprint = pprint.PrettyPrinter(indent = 4).pprint


#exec(open("functions.py").read())
from functions import *
from salt import salt

class acid(salt):
    classname = 'acid_noH'
    swap = False
    def __init__(self):
        salt.__init__(self)
        self.Nacid = 100
        
        idx = max(self.TYPES.values())+1
        self.TYPES['PHA'] = idx; idx+=1
        self.TYPES['PA'] = idx; idx+=1
        self.val['PA'] = -1 # valency of gel beads
        self.val['PHA'] = 0 # valency of gel beads

        self.NAMES = {}
        for key in self.TYPES.keys():
            val = self.TYPES[key]
            self.NAMES[val] = key
        
        self.p['K'] = 7.0  #[9.5, 9.0, 8.5, 8.0, 7.5, 7.0, 6.5, 6.0, ]
        #~ self.K_acid_es = self.K_acid*self.unit
      
        self.keys['md'] = ['pressure']
        # ~ if self.sigma: self.keys['md'] = ['pressure']
        # ~ else: self.keys['md'] = ['mindist']




    def __str__(self):
        self.classname = 'acidRE_noH'
        self.classname += '_Nacid'+str(self.Nacid)
        self.classname += '_box_l'+str(self.box_l)
        self.classname += self.swap*'_swap'
        return salt.__str__(self)
                

    
    def getbulk(self):
        s = salt()
        s.p['Na'] = self.p['Na']; 
        s.p['Cl'] = self.p['Cl']    
        s.p['Ca'] = self.p['Ca']    
        # ~ s.p = self.p
        # ~ try: del s.p['K'] 
        # ~ except KeyError: pass
        s.sigma = self.sigma; 
        s.lB = self.lB
        s.N_Samples = self.N_Samples
        s.eq_steps = self.eq_steps
        str(s)
        if abs(self.p['Cl']) != np.infty:
            try:
                bulk = s.load(scp = False)
                bulk.Pearson(keys = ['pressure', 'Na'])
                self.Posm = bulk.Means['pressure']
                self.Posm_err = bulk.Erros['pressure']
                self.cs_bulk = bulk.Means['Na']/bulk.volume/bulk.unit
                self.cs_bulk_err = bulk.Erros['Na']/bulk.volume/bulk.unit
            except FileNotFoundError:
                bulk = s
        else:
            
            bulk = s
            self.Posm = 0; self.Posm_err=0
            self.cs_bulk = 0; self.cs_bulk_err=0

                
        self.bulk = bulk
        return bulk
    

    def change_volume(self, target_l):
        print ('change_volume to the size L = ', target_l)
        #~ target_l = self.box_l
        box_l = self.system.box_l[0]
        
        while box_l != target_l:
            if target_l < box_l:    
                print ('compression to box_l = ', box_l)
                box_l = box_l*0.98
                if box_l<target_l: box_l = target_l
            else:
                print ('blowing up to box_l = ', box_l)
                box_l = box_l*1.05
                if box_l>target_l: box_l = target_l
            self.system.change_volume_and_rescale_particles(box_l)
            self.integrate();
            self.volume = box_l**3
            try: 
                self.WI.set_volume(self.volume)
                self.WI_params['volume']  = self.WI.get_volume()
            except AttributeError: pass
            try: 
                self.RE.set_volume(self.volume)
                self.RE_params['volume']  = self.RE.get_volume()
            except AttributeError: pass
            # ~ self.warmUp();
            
            print ('box_l = ', box_l)
        self.box_l = box_l
        
        print ('volume change done')

    def set_ionization(self):
        # This will run only if self.pK is set
        
        if abs(self.p['K']) != np.infty: 
            self.keys['re'] += ['PA']
            if not hasattr(self,'RE'):
                self.RE = reaction_ensemble.ReactionEnsemble(
                        temperature=1., 
                        exclusion_radius=self.exclusion_radius, 
                        seed = np.random.rand())
            
            
            #~ type_salt = self.TYPES[cation + anion]
            type_A  = self.TYPES['PA']
            type_AH   = self.TYPES['PHA']
            type_Na   = self.TYPES['Na']
            type_Ca   = self.TYPES['Ca']
            #~ type_OH   = self.TYPES['OH']
            #~ type_nodes   = self.TYPES['nodes']

            # ~ self.K_acid = 10**(-self.p['K']) #(mol/l)^1
            self.K_acid = self.unit*10**(-self.p['K']+self.p['H']-self.p['Na']) #(mol/l)^1
            
            Gamma = self.K_acid
            
            #~ Gamma_base = 1 / self.K_acid
            
            print ('Setting up gel reaction , Gamma = '+str(Gamma))
            CHARGES = {}
            CHARGES[type_A]  = -1
            CHARGES[type_AH] =  0
            CHARGES[type_Na]  = +1
            CHARGES[type_Ca]  = +2
            #~ CHARGES[type_OH]  = -1

            counterion_type = self.TYPES['Na']

            self.RE.add_reaction(gamma=Gamma,
                        reactant_types=[type_AH],
                        reactant_coefficients=[1],
                        product_types=[type_A, counterion_type],
                        product_coefficients=[1, 1],
                        default_charges=CHARGES
                        )
            if self.swap:
                self.RE.add_reaction(gamma=1,
                            reactant_types=[type_A, type_AH],
                            reactant_coefficients=[1, 1],
                            product_types=[type_AH, type_A],
                            product_coefficients=[1, 1],
                            default_charges=CHARGES
                            )
                
            # uncomment this if you want to add the reaction of two monomer units with one Ca ion
            if self.p['Ca'] != np.infty:
                counterion_type = self.TYPES['Ca']

                self.K_acid = self.unit*10**(-2*self.p['K']+2*self.p['H']-self.p['Ca']) #(mol/l)^1
                Gamma = self.K_acid
                self.RE.add_reaction(gamma=Gamma,
                            reactant_types=[type_AH],
                            reactant_coefficients=[2],
                            product_types=[type_A, counterion_type],
                            product_coefficients=[2, 1],
                            default_charges=CHARGES
                            )
            self.RE_params = self.RE.get_status()
            self.RE_params['volume'] = self.RE.get_volume()

    def get_alpha_ini(self):
        if 'H' in self.p.keys():
            pH = self.p['H']
            pK = self.p['K']
            if self.p['K'] == np.infty:
                alpha_ini = 0
            elif self.p['K'] == -np.infty:
                alpha_ini = 1
            else:
                alpha_ini = 1./(10**(-pH+pK)+1)
            self.alpha_ini = alpha_ini
        return alpha_ini
        
        
        
        

    
    def acid(self, alpha = 0):
        box_l = 5.
        volume = self.box_l**3
        self.system = espressomd.System(box_l = [self.box_l]*3)
        self.system.set_random_state_PRNG()

        self.system.time_step = self.time_step
        self.system.cell_system.skin = 0.4

        val = self.val['PA']
        
        type_HA = self.TYPES['PHA']
        type_A = self.TYPES['PA']
       
        for k in range(1, self.Nacid+1):
            pos = np.random.rand(3)*self.box_l
            if np.random.random() < alpha:
                unit = self.system.part.add(pos=pos, type=type_A, q = val)
            else:
                unit = self.system.part.add(pos=pos, type=type_HA)
        
        # Add counterions
    
        Q = int(sum(self.system.part[:].q))
        pos = np.random.rand(3)*self.box_l
        if Q<0:
            for i in range(-Q):
                if np.random.rand() < 10**(-self.p['Na'])/(10**(-self.p['Na'])+10**(-self.p['H'])): parttype = 'Na'
                else: parttype = 'H'
                self.system.part.add(pos = pos, type = self.TYPES[parttype], q = self.val[parttype])
        else:
            for i in range(Q):
                if np.random.rand() < 10**(-self.p['Cl'])/(10**(-p['Cl'])+10**(-self.p['OH'])): parttype = 'Cl'
                else: parttype = 'OH'
                self.system.part.add(pos = pos, type = self.TYPES['Cl'], q = self.val['Cl'])
        
        
        
        
        # ~ bond = interactions.FeneBond(k=10.0, d_r_max=2., r_0 = 0.)
        # ~ self.bond = bond
        # ~ self.system.bonded_inter.add(bond)
        
        
        
        
        
        self.integrate()
        self.system.setup_type_map(self.TYPES.values())

    def run(self):
        if self.sigma: 
            self.keys['md'] = ['pressure']
            self.update_md_samples = self.pressure
        else: 
            self.keys['md'] = ['mindist']
            self.update_md_samples = self.mindist

        self.__str__() # this updates the filenames
        print(self.fnamepkl)
        
        alpha_ini = self.get_alpha_ini()
        self.acid(alpha = alpha_ini)
        print(self.name)

        self.set_LJ()
        self.change_volume(self.box_l)        
        
        self.equilibrate()        
        #~ g.set_insertions(part_types = ['Na', 'Cl', 'H', 'OH'])
        self.set_insertions(part_types = ['Na', 'Cl'])
        self.set_ionization()

        self.set_EL()
        # ~ a.blowup()
        self.equilibrate()


        self.sample()
        self.Pearson(keys = self.keys['md']+self.keys['re']+self.keys['cph'])
         
        self.uptime = time.time() - self.tini
        self.save() 
        # ~ os.popen('cp '+self.name+'.pkl '+self.name+'final.pkl ')   
    
    
    def test(self):
        if self.sigma: 
            self.keys['md'] = ['pressure']
            self.update_md_samples = self.pressure
        else: 
            self.keys['md'] = ['mindist']
            self.update_md_samples = self.mindist

        self.__str__() # this updates the filenames
        print(self.fnamepkl)
        
        alpha_ini = self.get_alpha_ini()
        self.acid(alpha = alpha_ini)
        print(self.name)

        self.set_LJ()
        self.change_volume(self.box_l)        
        
        self.equilibrate()        
        #~ g.set_insertions(part_types = ['Na', 'Cl', 'H', 'OH'])
        self.set_insertions(part_types = ['Na', 'Cl'])
        # ~ self.set_ionizationRE()

        self.set_EL()
        # ~ a.blowup()
        self.equilibrate()

        # ~ self.sample()
        # ~ self.Pearson(keys = self.keys['md']+self.keys['re']+self.keys['cph'])
         
        # ~ self.uptime = time.time() - self.tini
        # ~ self.save()    

    def runfile(self):


        print(str(self))
        runfile = open(self.fnamerun,'w')
        runfile.write('import pickle\n');
        runfile.write('from gel import gel\n');


        runfile.write('pkl_file = open("'+self.fnamepkl+'", "rb")\n')
        runfile.write('g = pickle.load(pkl_file)\n')
        runfile.write('pkl_file.close()\n')
        runfile.write("g.run()\n");
        runfile.close()



    def seedscript(self):
        output = []
        output.append("#!espresso/es-build/pypresso")
        output.append("#!espresso/es-build/pypresso")
        # ~ output.append("#!venv/bin/python")
        output.append("from espressomd import reaction_ensemble")
        output.append("from acid import acid")
        output.append("from numpy import inf")
        
        output.append("a =acid()")
        output.append("a.lB = "+str(self.lB))
        output.append("a.sigma = "+str(self.sigma))
        # ~ output.append("a.exclusion_radius = "+str(self.exclusion_radius))

        output.append("a.Nacid = "+str(self.Nacid))
        # ~ output.append("g.alpha_ini = "+str(self.alpha_ini))
        output.append("a.box_l = "+str(self.box_l))
        
        if 'Cl' in self.p.keys():
            output.append("a.p['Cl'] = "+str(self.p['Cl']))
            output.append("a.p['Na'] = "+str(self.p['Na']))
                    
        if 'Ca' in self.p.keys():
            output.append("a.p['Ca'] = "+str(self.p['Ca']))
            
        if 'SO4' in self.p.keys():
            output.append("a.p['SO4'] = "+str(self.p['SO4']))

        if 'K' in self.p.keys():
            output.append("a.p['K'] = "+str(self.p['K']))
            output.append("a.p['H'] = "+str(self.p['H']))

        output.append("a.N_Samples = "+str(self.N_Samples))
        output.append("a.run()")
        
        infile = open(self.fnamepy, 'w') 
        for line in output:
            infile.write(line+'\n')
        infile.close()
        os.chmod(self.fnamepy, 0o774)

    def inherit(self, salt):
        for key in salt.__dict__.keys():
            if key in ['val', 'mu', 'p', 'TYPES', 'keys', 'steps', 'n_samples']:
                if key != 'keys':
                    exec('self.'+key+'.update(salt.'+key+')')
            else:
                exec('self.'+key+'=deepcopy(salt.'+key+')')
        return self
        
        
if __name__ == '__main__':
    import matplotlib.pyplot as plt
    # ~ import plotly.plotly as py
    # ~ import plotly.graph_objs as go
    pK_range = [7., 6., -np.infty]
    pK_range = [7.]
    # ~ pK_range = [7., 6., -np.infty]
    # ~ pK_range = [6.,7.]
    # ~ cs_range = [0.006, 0.15, 0.4,] # mol/l
    cs_range = [0.006, 0.15] # mol/l
    # ~ cs_range = [0., 0.006] # mol/l
    cs_range = [0.] # mol/l
    cs_range = [0.006] # mol/l
    # ~ cs_range = [1e-7] # mol/l
    # ~ cs_range = [0.15] # mol/l
    
    lB_range =  [0.,2.]
    lB_range =  [0.,]
    
    lB = 2.
    sigma = lB/2.
    # ~ sigma = 1.

    
    AA = {}
    N_Samples = 100
    BOX_L = np.linspace(14, 84, 36)
    # ~ BOX_L = np.linspace(14, 84, 11)
    for pK in pK_range:
        for cs in cs_range:
            
            # ~ BOX_L = np.linspace(14, 83)
            # ~ BOX_L = np.linspace(14, 83,70)  

            if cs!=0:
                # generate bulk
                s = salt()
                s.p['Na'] = -np.log10(cs)
                s.p['Cl'] = s.p['Na']
                s.lB = lB
                s.sigma = sigma
                # ~ s.exclusion_radius = s.sigma
                #!!!!!!!!! return this string back 
                s.N_Samples = N_Samples
                #!!!!!!!!! return this string back 
                str(s)
                # ~ s.send2metacentrum(run = True, mem = '1gb', walltime=192, hostname = 'tarkil')
                try:
                    bulk = s.load(scp = True)
                    cs_bulk = bulk.Means['Na'] / bulk.volume / bulk.unit
                except FileNotFoundError: 
                    pass
                    s.send2metacentrum(run = True, mem = '1gb', walltime=192, hostname = 'tarkil')
                    # ~ s.run()
            else: cs_bulk = 0
                        
            key = (cs, pK, lB)
            AA[key] = []
            # ~ BOX_L = np.linspace(84, 14, 36)
            
            # ~ BOX_L = [40.]
            for box_l in BOX_L:
                a = acid()
                
                a.box_l = box_l
                a.p['K'] = pK
                a.p['Na'] = -np.log10(cs)
                
                a.p['Cl'] = a.p['Na']
                a.p['H'] = 7.0

                a.N_Samples = N_Samples
                a.eq_steps = 1000
                a.lB = lB
                a.sigma = sigma
                # ~ a.exclusion_radius = a.sigma
                
                #~!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!~# return it back
                # ~ a.Nacid = g.MPC*16
                a.Nacid = 100
                print (str(a))
                # ~ a.run()
                try: 
                    a = a.load(scp = True)
                    try:
                        if len (a.Samples[a.keys['re'][0]]) >= a.N_Samples:
                            a.Pearson(a.keys['md']+a.keys['re']+a.keys['cph'])
                            AA[key].append(a)
                            a.getbulk()
                    except KeyError: pass
                except FileNotFoundError: 
                    pass
                    a.send2metacentrum(run = True, mem = '1gb', walltime=192, hostname = 'tarkil')
                    # ~ a.run()


            
        
            cspKkey = key[:2]
            color = colors[cspKkey]
            if key[-1] == 0: # lB == 0
                color = color[:-2]+'7d' 
                    
            
            figsize = 3.5

            label = r'$c^{bulk}_s$ = '+'{:.3f} mol/l'.format(cs_bulk)+r', $\mathrm{p}K = $'+str(pK)+r', $l_B = $'+str(lB)
            # ~ label = r'temp'
            # ~ plot4Borisov(GG[key])
            # ~ plotP(AA[key], label)
            plotAlpha(AA[key], label)

    fig_alpha.savefig('figures/acid_alpha.pdf')
    fig_PV.savefig('figures/acid_pressure.pdf')

    # ~ fig_alpha.savefig('figures/gel_alpha.pdf')
    # ~ fig_PV.savefig('figures/gel_pressure.pdf')



    DICT = getData2Plot(AA[key])    
    csvfilename = "data/acid_cs%s_pK%s_lB%s.csv"%(key[0], key[1], lB)
    with open(csvfilename, 'w') as csvfile: 
        for csvkey in DICT.keys(): 
            if len(DICT[csvkey]) == 2:
                string_title = csvkey
                string_data0 = array2csv(DICT[csvkey][0])
                string_data1 = array2csv(DICT[csvkey][1])
                
                csvfile.write("%s, %s\n"%(csvkey, string_data0))
                csvfile.write("%s, %s\n"%(csvkey+'_err', string_data1))
            else:
                string_data = array2csv(DICT[csvkey])
                csvfile.write("%s, %s\n"%(csvkey, string_data))





