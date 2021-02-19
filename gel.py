###################################################
#  The most simple setup of Reaction  Ensemble
###################################################
from __future__ import print_function
import espressomd
import socket
from espressomd import interactions, electrostatics, visualization, reaction_ensemble
from copy import copy, deepcopy
from multiprocessing import Process, Queue

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


#~ exec(open("functions.py").read())
# ~ from functions import *
from salt import salt
from base import base
from acid import acid
from functions import *
#exec(open('functions.py').read())


def sfunc(qi,qo):
    global LS
    # ~ sys.stdout = open(str(os.getpid()) + ".out", "w")

    sys.stdout = open("sfunc.out", "w", buffering=1)

    s = salt()
    s.box_l = Ls
    s.volume = s.box_l**3
    # ~ s.p['Na'] = -np.log10(0.15)
    # ~ s.p['Cl'] = s.p['Na']


    s.eq_steps = eq_steps
    s.lB = lB
    s.sigma = sigma

    s.__str__() # this updates the filenames
    s.init_es()



    # ~ s.set_insertions(part_types = ['Na', 'Cl'])

    s.system.setup_type_map(s.TYPES.values() )




    pos = np.random.random(3) * s.box_l
    s.system.part.add(pos=pos, type=s.TYPES['Cl'], q=s.val['Cl'])
    pos = np.random.random(3) * s.box_l
    s.system.part.add(pos=pos, type=s.TYPES['Na'], q=s.val['Na'])

    s.set_LJ()
    s.equilibrate()
    s.set_EL()
    s.equilibrate()

    choices = [s.sampleMD]*bool(s.sigma)
    # if sigma is not zero then add 'pressure' to the list of mdkeys
    s.keys['md'] = ['pressure']*bool(s.sigma)
    #a = 1
    #print('sampling salt', a ,' times')
    #for i in range(a):    np.random.choice(choices)()

    Eini = s.energy()
    NCl = s.system.number_of_particles(s.TYPES['Cl'])
    NNa= s.system.number_of_particles(s.TYPES['Na'])
    N = [NCl, NNa]
    DE = 0
    V = s.volume
    s.current_state = [DE, V, N]

    while True:
        xi = qi.get()
        # ~ print ('sfunc xi', xi)
        Eini = s.energy()
        if xi<0:
            # here pair is type list of list [aid, apos, av, atype, aq]
            pair = s.removePair()
            #try:

            #except ValueError:
            #    pass
        else:
            # here pair is type list of espresso particles
            pair = s.addPair()
        NCl = s.system.number_of_particles(s.TYPES['Cl'])
        NNa = s.system.number_of_particles(s.TYPES['Na'])
        N = [NCl, NNa]
        E = Eini - s.energy()
        V = s.volume
        qo.put([E, V, N])
        print ('Cl particles in salt', NCl, 'salt volume', round(V))
        accept = qi.get()
        if accept:
            s.current_state = [E, V, N]
            # ~ qo.put(s.current_state)
        else:
            # ~ qo.put(s.current_state)
            if xi<0:
                [aid, apos, av, atype, aq] = pair[0]
                [bid, bpos, bv, btype, bq] = pair[1]
                s.system.part.add(pos=apos, type=atype, q=aq, v=av)
                s.system.part.add(pos=bpos, type=btype, q=bq, v=bv)
            else:
                [a,b] = pair
                a.remove()
                b.remove()



class gel(acid,salt):
    classname = 'gel_noH'
    def __init__(self):
        acid.__init__(self)
        self.MPC = 30 # the length of the strands of the gel network
        self.Ngel = self.MPC*16 + 8

        idx = max(self.TYPES.values())+1
        self.TYPES['nodes'] = idx; idx+=1
        self.val['nodes'] = 0 # valency of gel beads

        self.NAMES = {}
        for key in self.TYPES.keys():
            val = self.TYPES[key]
            self.NAMES[val] = key


        Rekeys = []
        for i in range(16):
            Rekeys.append('Re{:02d}'.format(i))
        self.keys['md'] = Rekeys+ ['pressure']
        #self.keys['re'] = ['mindist']
        self.keys['re'] = []
        # ~ if self.sigma: self.keys['md'] += ['pressure']

    def __str__(self):
        self.classname = 'gel'
        # ~ self.classname = 'gelRE_noH_withoutCa'
        self.classname += '_MPC'+str(self.MPC)
        self.classname += '_box_l'+str(self.box_l)
        self.classname += self.swap*'_swap'
        return salt.__str__(self)

    def update_re_samples(self):
        self.getN(keys = self.keys['re'])
        #type_ca = type_pa = 'default'
        #if self.p['Ca'] != np.infty:
            #type_ca = [self.TYPES['Ca']]
            #type_pa = [self.TYPES['PA']]
            #self.mindist(p1 = type_ca, p2=type_pa)

    def update_md_samples(self):
        ''' returns the Re and pressure( if sigma is not zero)'''
        # ~ Re = self.calc_Re()
        # ~ pressure = self.pressure()
        #fl = [self.calc_Re, self.pressure]
        fl = [self.calc_Re_all, self.pressure]

        return [f() for f in fl]



    def sampleGibbsEnsemble(self,NCltot, Lbox):
        global Lg, Ls, eq_steps, lB, sigma
        Lg = self.box_l
        Ls = (Lbox**3 - Lg**3)**(1./3)
        eq_steps = self.eq_steps
        lB = self.lB
        sigma = self.sigma




        gel = self
        siqueue = Queue()
        soqueue = Queue()
        sproc = Process(target=sfunc, args=(siqueue, soqueue))
        sproc.start()

        Eini = gel.energy()
        NClgel = gel.system.number_of_particles(gel.TYPES['Cl'])
        NNagel = gel.system.number_of_particles(gel.TYPES['Na'])
        N = [NClgel, NNagel]
        DE = 0
        V = gel.volume
        gel.current_state = [DE, V, N]

        while True:
            xi = np.random.choice([1,-1])
            Eini = gel.energy()
            if xi>0:
                try:
                    pair = gel.removePair()
                except ValueError:
                    pass
            else:
                pair = gel.addPair()

            NCl = gel.system.number_of_particles(gel.TYPES['Cl'])
            NNa = gel.system.number_of_particles(gel.TYPES['Na'])
            Ng = [NCl, NNa]
            Eg = Eini - gel.energy()
            Vg = gel.volume





            siqueue.put(xi)
            [Es, Vs, Ns] = soqueue.get()
            #  emulates heaviside function

            acceptance = -Es-Eg+xi*( np.log(Vs/Vg) + np.log((Ng[0]+np.heaviside(xi,0))/((Ns[0]+np.heaviside(-xi,0)))) + np.log((Ng[1]+np.heaviside(xi,0))/((Ns[1]+np.heaviside(-xi,0))) ))
            acceptance = np.exp(acceptance)
            accept = acceptance > np.random.rand()
            print(acceptance, accept)
            siqueue.put(accept)
            giqueue.put(accept)


    def diamond(self, alpha = 0):
        """ Generates a diamond network made of 8 nodes and 16 connecting chains.
            Chains are fully stretched; the distance between beads is 1.
            Note, this will change the box_l.

        Parameters
        ----------
        alpha : :obj:`int`, optional
            Ionization degree of a newly created network.
            Charges will be distributed randomly so that the number of charged to the total number of beads is approx alpha
            Defaults to 0, which means that there will be no charges on chains
        """

        box_l = 5.
        volume = self.box_l**3
        self.system = espressomd.System(box_l = [self.box_l]*3)
        #self.system.set_random_state_PRNG()

        self.system.time_step = self.time_step
        self.system.cell_system.skin = 0.4

        val = self.val['PA']

        #~ val_nodes = val
        val_nodes = 0

        # set the box_size
        bond_length = 1.0
        lat_fac = 4.0/(3.0)**0.5*bond_length  # What is lat_fac
        box_l = lat_fac*(self.MPC+1.0)
        self.system.box_l = [box_l]*3
        print(self.system.box_l)

        type_nodes = self.TYPES['nodes']
        type_chains = self.TYPES['PHA']
        type_charges = self.TYPES['PA']

        type_ids = [type_nodes, type_chains, type_charges]
        #self.system.setup_type_map(type_ids)
        # set the bonded interaction between the gel beads
        bond = interactions.FeneBond(k=10.0, d_r_max=2., r_0 = 0.)
        #~ bond = interactions.HarmonicBond(k=7.0, r_0 = 1.)
        self.bond = bond
        self.system.bonded_inter.add(bond)
        #~ self.tune_skin()

        # place 8 tetra-functional nodes
        dnodes = np.array([
            [0, 0, 0], [1, 1, 1],
            [2, 2, 0], [0, 2, 2],
            [2, 0, 2], [3, 3, 1],
            [1, 3, 3], [3, 1, 3]])
        dnodes =  dnodes  * box_l / 4.

        nodes_ids = []

        dchain = np.array([
            [0, 1, +1, +1, +1],
            [1, 2, +1, +1, -1],
            [1, 3, -1, +1, +1],
            [1, 4, +1, -1, +1],
            [2, 5, +1, +1, +1],
            [3, 6, +1, +1, +1],
            [4, 7, +1, +1, +1],
            [5, 0, +1, +1, -1],
            [5, 3, +1, -1, +1],
            [5, 4, -1, +1, +1],
            [6, 0, -1, +1, +1],
            [6, 2, +1, -1, +1],
            [6, 4, +1, +1, -1],
            [7, 0, +1, -1, +1],
            [7, 2, -1, +1, +1],
            [7, 3, +1, +1, -1]]);

        # place intermediate monomers on chains connecting the nodes */

        off = bond_length / 3.**0.5
        dpos = {}
        nodes = []
        for pos in dnodes:
            nodes.append(self.system.part.add(pos=pos, type=type_nodes, q = val_nodes))
            cur_id = self.system.part.highest_particle_id
            nodes_ids.append(cur_id)
        #~ self.nodes_ids = nodes_ids
        # Place intermediate monomers on chains connecting the nodes */
        #~ chains = [[]] * (2*8)

        pos = [0, 0, 0]

        chains = []
        for i in range(2*8):
            chain = []
            nodeid  = dchain[i][0]
            chain.append(self.system.part[nodeid])
            for k in range(1, self.MPC+1):
                for j in range(3):
                    pos[j] = dnodes[dchain[i][0]][j] + k * dchain[i][2 + j] * off;
                if np.random.random() < alpha:
                    unit = self.system.part.add(pos=pos, type=type_charges, q = val)
                else:
                    unit = self.system.part.add(pos=pos, type=type_chains)
                # ~ if k%cM_dist==0:
                    # ~ unit = self.system.part.add(pos=pos, type=type_charges, q = val)
                # ~ else:
                    # ~ unit = self.system.part.add(pos=pos, type=type_chains)
                chain.append(unit)
                unit.add_bond((bond, chain[k-1]))
            nodeid  = dchain[i][1]
            unit.add_bond((bond, nodeid))
            chains.append(chain)

        # Add counterions

        Q = int(sum(self.system.part[:].q))
        counterion = 'Na'
        for i in range(-Q):
            pos = np.random.rand(3)*self.system.box_l[0]
            self.system.part.add(pos = pos, type = self.TYPES[counterion], q = self.val[counterion])

        print('###################', val)
        self.integrate()
        #~ self.save()
        #~ self.blender()
        self.dchain = dchain

        self.system.setup_type_map(self.TYPES.values() )


    def calc_Re(self):
        #~ calc_re(self, chain_start=None, number_of_chains=None, chain_length=None)
        pairs = self.dchain[:,0:2]
        D = np.array([])
        for pair in pairs:
            pos1 = self.system.part[pair[0]].pos
            pos1 = pos1 % self.box_l # this makes coordinates folded
            pos2 = self.system.part[pair[1]].pos
            pos2 = pos2 % self.box_l # this makes coordinates folded
            # ~ Dvec = pos1 - pos2
            Dvec =  abs(pos1 -pos2) - (abs((pos1 -pos2)) >  self.box_l/2 )*self.box_l  # this checks if the distance vector coordinates are bigger than the half of box_l and if yes substitute  box_l from the cootrdinate
            # ~ Dvec = (abs(pos2-pos1)>abs(pos2-pos1+g.box_l))*g.box_l - (pos2-pos1)
            D = np.append(D, np.linalg.norm(Dvec))
            # ~ D = np.append(D, np.linalg.norm(pos2 - pos1))

        Re = np.mean(D)
        try:
            self.samples['Re'] = np.append(self.samples['Re'], Re)
        except KeyError:
            self.samples['Re'] = np.array([Re])
        return Re
        #~ return [np.mean(D), np.std(D)]


    def calc_Re_all(self):
        #~ calc_re(self, chain_start=None, number_of_chains=None, chain_length=None)
        pairs = self.dchain[:,0:2]
        D = np.array([])
        pairid = 0
        for pair in pairs:
            pos1 = self.system.part[pair[0]].pos
            pos1 = pos1 % self.box_l # this makes coordinates folded
            pos2 = self.system.part[pair[1]].pos
            pos2 = pos2 % self.box_l # this makes coordinates folded
            # ~ Dvec = pos1 - pos2
            # this checks if the distance vector coordinates are bigger than the half of box_l and if yes substitute  box_l from the cootrdinate
            Dvec =  abs(pos1 -pos2) - (abs((pos1 -pos2)) >  self.box_l/2 )*self.box_l
            # ~ Dvec = (abs(pos2-pos1)>abs(pos2-pos1+g.box_l))*g.box_l - (pos2-pos1)
            Rei = np.linalg.norm(Dvec)
            D = np.append(D, Rei)

            try:
                self.samples['Re{:02d}'.format(pairid)] = np.append(self.samples['Re{:02d}'.format(pairid)], Rei)
            except (KeyError, ValueError):
                self.samples['Re{:02d}'.format(pairid)] = np.array([Rei])
            pairid += 1
        Re = np.mean(D)
        return D


    def run(self):
        tini = time.time()
        self.__str__() # this updates the filenames
        print(self) # this updates the filenames
        alpha_ini = self.get_alpha_ini()

        self.diamond(alpha = alpha_ini)
        self.system.setup_type_map(list(self.TYPES.values()))
        # ~ print(g.name)
        self.set_insertions()
        self.set_ionization()

        self.minimize_energy()
        self.set_thermostat()

        self.set_LJ()
        self.minimize_energy()


        self.change_volume(self.box_l)
        self.minimize_energy()

        self.equilibrate(eq_steps = 10)
        for i in range (100): self.RE.reaction(reaction_steps = 10000); print(self.getN(self.keys['re']))

        self.set_EL()
        self.minimize_energy()


        self.equilibrate()
        self.sample()

        self.Pearson(keys = self.keys['md']+self.keys['re'])
        self.uptime = time.time() - tini
        self.save()






    def Raju(self):
        files = [ 'Raju/gel_PvsBox_l.out']
        colors = ['green', 'red', 'blue']
        for f in range(len(files)):
            data  = open(files[f]).read()

            data = data.split('\n')
            data = data[1:-1]
            for i in range(len(data)):
                data[i] = data[i].split(" ")
            data = np.array(data, dtype = float)
            data = data.T
            P = data[1]
            box_l = data[0]
            P_err = data[2]
        return [box_l, P, P_err]

    def AK(self, pK):
        files = {10: 'AK/wgel_mpc30_pK10.out',
                 11: 'AK/wgel_mpc30_pK11.out',
                 5:  'AK/wgel_mpc30_pK5.out',
                 6: 'AK/wgel_mpc30_pK6.out',
                 7: 'AK/wgel_mpc30_pK7.out',
                 8: 'AK/wgel_mpc30_pK8.out',
                 9: 'AK/wgel_mpc30_pK9.out', }


        data  = open(files[pK]).read()

        data = data.split('\n')
        data = data[1:-1]
        for i in range(len(data)):
            data[i] = data[i].split(" ")
        data = np.array(data, dtype = float)
        data = data.T
        P = data[1]
        NA = data[3]
        NAerr = data[4]
        box_l = data[0]
        P_err = data[2]

        return [box_l, P, P_err, NA, NAerr]


    def seedscript(self):

        output = []
        output.append("#!espresso/es-build/pypresso")
        output.append("#!espresso/es-build/pypresso")
        # ~ output.append("#!venv/bin/python")
        output.append("import sys, os")
        output.append("os.chdir('/home/{}/mv')".format(self.USERNAME))
        output.append("sys.path.append('/home/{}/mv')".format(self.USERNAME))
        output.append("from espressomd import reaction_ensemble")
        output.append("from gel import gel")
        output.append("from numpy import inf")

        output.append("g =gel()")
        output.append("g.lB = "+str(self.lB))

        output.append("g.sigma = "+str(self.sigma))
        output.append("g.epsilon = "+str(self.epsilon))

        # ~ output.append("g.alpha_ini = "+str(self.alpha_ini))
        output.append("g.box_l = "+str(self.box_l))
        output.append("g.eq_steps = "+str(self.eq_steps))
        if self.swap: output.append("g.swap = True")
        if 'Na' in self.p.keys():
            output.append("g.p['Cl'] = "+str(self.p['Cl']))
            output.append("g.p['Na'] = "+str(self.p['Na']))

        if 'Ca' in self.p.keys():
            output.append("g.p['Ca'] = "+str(self.p['Ca']))

        if 'SO4' in self.p.keys():
            output.append("g.p['SO4'] = "+str(self.p['SO4']))

        if 'K' in self.p.keys():
            output.append("g.p['K'] = "+str(self.p['K']))
            output.append("g.p['H'] = "+str(self.p['H']))

        output.append("g.N_Samples = "+str(self.N_Samples))
        output.append("g.run()")

        infile = open(self.fnamepy, 'w')
        for line in output:
            infile.write(line+'\n')
        infile.close()
        os.chmod(self.fnamepy, 0o774)




if __name__ == '__main__':






    cs = 0.15



    g =gel()
    g.lB = 2.0
    g.eq_steps = 100
    g.sigma = 1.0
    #g.swap = True
    g.exclusion_radius = 1.0
    g.box_l = 80.5
    g.p['Cl'] = -np.log10(cs)
    #g.steps['md'] = 64
    #g.steps['re'] = 32
    
    #g.p['Na'] = -np.log10(cs)

    g.p['Na'] = -np.log10(cs*0.873)
    g.p['Ca'] = -np.log10(cs*0.114)    
    
    g.p['K'] = 3.0
    g.p['H'] = 7.0
    g.N_Samples = 200
    g.run()








1
