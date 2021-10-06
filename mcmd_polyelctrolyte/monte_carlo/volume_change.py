from typing import Tuple
import numpy as np
import pandas as pd
import math
import random
import time

from .libmontecarlo import AbstractMonteCarlo
from .libmontecarlo import StateData, ReversalData, AcceptCriterion


def _random_volume_change(V_max : float) -> float:
    """Returns random value from uniform distribution

    Args:
        V_max (float): defines range [-V_max, V_max]

    Returns:
        float: random volume
    """    
    vol = random.uniform(-V_max, V_max)
    return vol

def get_tau(x, acf_n_lags : int = 200):
    from statsmodels.tsa.stattools import acf
    import numpy as np
    acf = acf(x, nlags = acf_n_lags)
    tau_int =1/2+max(np.cumsum(acf))    
    return tau_int

def correlated_data_mean_err(x, tau, ci = 0.95):
    import scipy.stats
    import numpy as np
    x_mean = np.mean(x)
    n_eff = np.size(x)/(2*tau)
    print(f"Effective sample size: {n_eff}")
    t_value=scipy.stats.t.ppf(1-(1-ci)/2, n_eff)
    print(f"t-value: {t_value}")
    err = np.std(x)/np.sqrt(n_eff) * t_value
    return x_mean, err

SIDES = [0,1]
PAIR = [0,1]
CHARGES=[-1,1]
MOBILE_SPECIES = [0,1]


class MonteCarloVolume(AbstractMonteCarlo):
    def __init__(self, server, p_ext=0):
        super().__init__()
        self.server = server
        self.p_ext = 0
        self.setup()

    def setup(self) -> StateData:
        request_body = [
            "potential_energy()",
            "system.box_l"
            ]
        system_init_state_request=self.server(request_body,SIDES)
        energy, box_l = [
            [result.result()[i] for result in system_init_state_request] 
                for i in range(len(request_body))
                ]

        volume = [float(np.prod(box_l[i])) for i in SIDES]
        
        
        new_state = StateData(
            energy = energy, 
            volume = volume,
            box_l = box_l
            )
        
        self.current_state = new_state
        return new_state

    def move(self) -> Tuple[ReversalData, AcceptCriterion]:
        V_max=min(self.current_state['volume'])*0.05
        dV = _random_volume_change(V_max)
        
        #increment(decrement) volume in salt on -dV and add dV to gel,
        #get new potential energy
        request = [self.server(
                        [
                        "increment_volume({dV}*(-1.0))",
                        "system.box_l[0]"
                        ],
                         0
                    ),
                    self.server(
                        [
                        "increment_volume({dV})",
                        "system.box_l[1]"
                        ],
                         1
                    ),
            ]
        
        new_energy = [request_.result()[0] for request_ in request]
        new_box_l = [request_.result()[1] for request_ in request]
        new_volume = [float(np.prod(new_box_l[i])) for i in SIDES]

        reversal_data =  ReversalData(
            volume = new_volume,
            box_l = new_box_l
            energy = new_energy)

        accept_criterion = AcceptCriterion(
            dE = sum(new_energy) - sum(self.current_state['energy']),
            p_ext = self.p_ext,
            dV=dV,
            beta = 1
            )

        return reversal_data, accept_criterion
    

    def update_state(self, reversal: ReversalData):
        update_c_state = StateData(
            energy = reversal['energy'],
            
        )
        self.current_state.update(update_c_state)

    def reverse(self, reversal_data: ReversalData):
        side = reversal_data['side']
        other_side = int(not(side))
        self.server([
            f"add_particle(['id'], q = {CHARGES[i]}, type = {i}, **{reversal_data['removed'][i]})"
            for i in PAIR
            ], side)
        
        self.server([
            f"remove_particle({reversal_data['added'][i]['id']},['id'])" 
            for i in PAIR
            ], other_side)