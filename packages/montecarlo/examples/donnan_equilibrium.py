# %%
from typing import Tuple
import numpy as np
import random
import matplotlib.pyplot as plt
from montecarlo import AbstractMonteCarlo
from montecarlo import StateData, ReversalData, AcceptCriterion
from sample_to_target import sample_to_target

from analytic_donnan import speciation_inf_reservoir, zeta_compressed
# %%
SIDES = [0, 1]


def _entropy_change(anion_0, anion_1, cation_0, cation_1, volume_0, volume_1, removed_from=0):
    if removed_from == 0:
        return np.log((volume_1/volume_0)**2 * (anion_0*cation_0)/((anion_1+1)*(cation_1+1)))
    elif removed_from == 1:
        return _entropy_change(anion_1, anion_0, cation_1, cation_0, volume_1, volume_0, 0)


class MonteCarloDonnan(AbstractMonteCarlo):

    def __init__(self, N_pairs: Tuple, A_fixed: int, Volumes: Tuple):
        super().__init__()
        self.anion = list(N_pairs)
        self.cation = [N_pairs[0], N_pairs[1]+A_fixed]
        self.volume = list(Volumes)
        self.v = Volumes[1]/sum(Volumes)
        self.current_state = dict(
            v=self.v,
            zeta=(self.anion[0]/self.volume[0])/(self.anion[0]/self.volume[1]),
            product=[anion*cation/volume**2 for anion, cation,
                     volume in zip(self.anion, self.cation, self.volume)]
        )

    def move(self) -> Tuple[ReversalData, AcceptCriterion]:
        #side = int(random.random()>(self.anion[0]+self.cation[0])/(sum(self.anion)+sum(self.cation)))
        side = random.choice(SIDES)
        other_side = int(not(side))
        # print(*self.anion)

        #n1=self.anion[side] + self.cation[side]
        #n2=self.anion[other_side] + self.cation[other_side]
        #v1 = self.volume[side]
        #v2 = self.volume[other_side]
        delta_S = _entropy_change(
            *self.anion, *self.cation, *self.volume, side)
        #print(f'Entropy change: {delta_S}')

        # move pair
        # remove pair
        self.anion[side] = self.anion[side]-1
        self.cation[side] = self.cation[side]-1
        # add pair
        self.anion[other_side] = self.anion[other_side]+1
        self.cation[other_side] = self.cation[other_side]+1

        accept_criterion = AcceptCriterion(
            dE=0,  # no interaction
            dS=delta_S,
            beta=1
        )

        reversal_data = ReversalData(
            side=side)

        #print(f'[{side}]->[{other_side}, {delta_S}]')
        return reversal_data, accept_criterion

    def reverse(self, reversal_data: ReversalData):
        side = reversal_data['side']
        other_side = int(not(side))

        # move pair
        # add removed
        self.anion[side] = self.anion[side]+1
        self.cation[side] = self.cation[side]+1
        # remove added
        self.anion[other_side] = self.anion[other_side]-1
        self.cation[other_side] = self.cation[other_side]-1

    def update_state(self, reversal: ReversalData):
        self.current_state = dict(
            v=self.v,
            zeta=(self.anion[1]/self.volume[1])/(self.anion[0]/self.volume[0]),
            product=[anion*cation/volume**2 for anion, cation,
                     volume in zip(self.anion, self.cation, self.volume)]
        )

    def sample_zeta(self, sample_size: int):
        zetas = []
        for i in range(sample_size):
            zetas.append(self.step()['zeta'])
        return zetas

def zeta_from_monte_carlo(N_pairs, fixed_anions, v):
    mc = MonteCarloDonnan(
        (N_pairs*(1-v), N_pairs*v),
        fixed_anions,
        (1-v, v))
    # equilibration steps
    [mc.step() for i in range(N_pairs*4)]
    zeta = sample_to_target(mc.sample_zeta, target_eff_sample_size = 30)
    return zeta[0]
# %%
if __name__ == "__main__":
    c_s = 0.005 #part per sigma^3
    fixed_anion = 488
    gel_init_vol = 39**3
    v = np.linspace(0.2, 0.8, 11)
    zeta_an = [zeta_compressed(c_s,fixed_anion, gel_init_vol, v_) for v_ in v]
    N_pairs = round(speciation_inf_reservoir(c_s, fixed_anion, gel_init_vol)[0])
#%%

    from multiprocessing import Pool
    def worker(vol):
        return zeta_from_monte_carlo(N_pairs, fixed_anion, vol)
    with Pool(5) as p:
        zeta = p.map(worker, v)
    plt.scatter(v, zeta, marker='s')

    plt.plot(v, zeta_an)
    plt.xlabel("v")
    plt.ylabel("zeta")
    plt.show()

# %%
