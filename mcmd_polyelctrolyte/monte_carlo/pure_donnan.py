#%%
from typing import Tuple
import numpy as np
import pandas as pd
import math
import random
import time
import matplotlib.pyplot as plt

from libmontecarlo import AbstractMonteCarlo
from libmontecarlo import StateData, ReversalData, AcceptCriterion

SIDES = [0,1]

def _entropy_change(N1, N2, V1, V2, n=1):
    #N1, V1 - box we removing particle from
    #N2, V2 - box we adding to
    #n - number of particles 
    if n==1:
        return math.log((N1*V2)/((N2+1)*V1))
    elif n==2:
        return math.log((V2/V1)**2*(N1*(N1-1))/((N2+2)*(N2+1)))

class MonteCarloDonnan(AbstractMonteCarlo):

    def __init__(self, N_pairs : Tuple, A_fixed : int, Volumes : Tuple):
        super().__init__()
        self.anion = list(N_pairs)
        self.cation = [N_pairs[0], N_pairs[1]+A_fixed]
        self.volume = list(Volumes)
        self.v = Volumes[1]/sum(Volumes)
        self.current_state = dict(
            v = self.v,
            zeta = (self.anion[0]/self.volume[0])/(self.anion[0]/self.volume[1])
        )

    def move(self) -> Tuple[ReversalData, AcceptCriterion]:
        side = random.choice(SIDES)
        other_side = int(not(side))

        n1=self.anion[side] + self.cation[side]
        n2=self.anion[other_side] + self.cation[other_side]
        v1 = self.volume[side]
        v2 = self.volume[other_side]
        delta_S = _entropy_change(n1,n2,v1,v2,2)
        #print(f'Entropy change: {delta_S}')

        ##move pair
        #remove pair
        self.anion[side] = self.anion[side]-1
        self.cation[side] = self.cation[side]-1
        #add pair
        self.anion[other_side] = self.anion[other_side]+1
        self.cation[other_side] = self.cation[other_side]+1

        accept_criterion = AcceptCriterion(
            dE = 0, #no interaction
            dS = delta_S,
            beta = 1
            )
        
        reversal_data =  ReversalData(
            side = side)
        
        return reversal_data, accept_criterion

    def reverse(self, reversal_data: ReversalData):
        side = reversal_data['side']
        other_side = int(not(side))

                ##move pair
        #add removed 
        self.anion[side] = self.anion[side]+1
        self.cation[side] = self.cation[side]+1
        #remove added
        self.anion[other_side] = self.anion[other_side]-1
        self.cation[other_side] = self.cation[other_side]-1
    
    def update_state(self, reversal: ReversalData):
        self.current_state = dict(
            v = self.v,
            zeta = (self.anion[1]/self.volume[1])/(self.anion[0]/self.volume[0])
        )
#%%
N_pairs = (100,100)
A_fix = 248*0.5
v = 0.5
Volume = (200*(1-v), 200*(v))
mc = MonteCarloDonnan(N_pairs, A_fix, Volume)
# %%
def get_zeta(v):
    vol = sum(mc.volume)
    mc.volume = [vol*(1-v), vol*v]
    zeta = []
    for i in range(100000):
        mc.step()
    for k in range(500):
        for i in range(1000):
            mc.step()
        zeta.append(mc.current_state['zeta'])
    return np.mean(zeta), np.std(zeta)
#%%
vv = np.linspace(0.2, 0.8, 9)
zetas = [get_zeta(v_)[0] for v_ in vv]
# %%
plt.plot(vv, zetas)