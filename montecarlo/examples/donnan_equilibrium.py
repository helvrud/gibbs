# %%
from typing import Tuple
import numpy as np
import random
import matplotlib.pyplot as plt
from montecarlo import AbstractMonteCarlo
from montecarlo import StateData, ReversalData, AcceptCriterion
from montecarlo import get_tau, sample_to_target_error
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

# %%


def zeta_from_monte_carlo(N_pairs, fixed_anions, v):
    mc = MonteCarloDonnan(
        (N_pairs*(1-v), N_pairs*v),
        fixed_anions,
        (1-v, v))
    # equilibration steps
    [mc.step() for i in range(N_pairs*4)]
    zeta = sample_to_target_error(mc.sample_zeta, 0.002)
    return zeta[0]


def zeta_from_analytic(N_pairs, fixed_anions, v):
    import numpy as np
    if v == 0.5:
        v = 0.49999999  # dirty
    sqrt = np.sqrt
    return v*(N_pairs - (fixed_anions*(1 - v)**2/2 + N_pairs*v**2 - (1 - v)*sqrt(fixed_anions**2*(1 - v)**2 + 4*fixed_anions*N_pairs*v**2 + 4*N_pairs**2*v**2)/2)/(v**2 - (1 - v)**2))/((1 - v)*(fixed_anions + (fixed_anions*(1 - v)**2/2 + N_pairs*v**2 - (1 - v)*sqrt(fixed_anions**2*(1 - v)**2 + 4*fixed_anions*N_pairs*v**2 + 4*N_pairs**2*v**2)/2)/(v**2 - (1 - v)**2)))


def zeta_analytic(N_pairs, fixed_anions, v_salt, v_gel):
    from analytic_donnan import speciation
    anions_salt, anions_gel, * \
        r = speciation(N_pairs, fixed_anions, v_salt, v_gel)
    zeta = anions_gel*v_salt/(anions_salt*v_gel)
    return zeta


if __name__ == "__main__":
    N_pairs = 100
    fixed_anion = 50
    v = np.linspace(0.2, 0.8, 11)
    zeta_an = [zeta_from_analytic(N_pairs, fixed_anion, v_) for v_ in v]
    zeta_an2 = [zeta_analytic(N_pairs, fixed_anion, 1-v_, v_) for v_ in v]
    from multiprocessing import Pool

    def worker(v):
        return zeta_from_monte_carlo(N_pairs, fixed_anion, v)
    with Pool(5) as p:
        zeta = p.map(worker, v)
    plt.scatter(v, zeta, marker='s')
    plt.plot(v, zeta_an)
    plt.plot(v, zeta_an2)
    plt.xlabel("v")
    plt.ylabel("zeta")
    plt.show()

# %%
