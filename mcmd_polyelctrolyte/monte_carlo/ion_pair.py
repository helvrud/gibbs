#%%
from typing import Tuple
import numpy as np
import pandas as pd
import math
import random
import time

from .libmontecarlo import AbstractMonteCarlo
from .libmontecarlo import StateData, ReversalData, AcceptCriterion


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

def _rotate_velocities_randomly(velocities):
    from scipy.spatial.transform import Rotation
    rot = Rotation.random().as_matrix
    velocities_rotated = [list(rot().dot(velocity)) for velocity in velocities]
    return velocities_rotated
#def _entropy_change(N1, N2, V1, V2, n=1):
    #N1, V1 - box we removing particle from
    #N2, V2 - box we adding to
    #n - number of particles 
#    if n==1:
#        return math.log((N1*V2)/((N2+1)*V1))
#    elif n==2:
#        return math.log((V2/V1)**2*(N1*(N1-1))/((N2+2)*(N2+1)))

def _entropy_change(anion_0, anion_1, cation_0, cation_1, volume_0, volume_1, removed_from = 0):
    if removed_from == 0:
        return math.log((volume_1/volume_0)**2   *   (anion_0*cation_0)/((anion_1+1)*(cation_1+1)))
    elif removed_from == 1:
        return _entropy_change(anion_1, anion_0, cation_1, cation_0, volume_1, volume_0, 0)

#def _get_mobile_species_count(particles_info_df, grouper = ['type','side']):
#    return particles_info_df.loc[
#        particles_info_df.type.isin(MOBILE_SPECIES)
#        ].groupby(by=grouper).size()

class MonteCarloPairs(AbstractMonteCarlo):
    def __init__(self, server):
        super().__init__()
        self.server = server
        self.setup()

    def setup(self) -> StateData:
        request_body = [
            "potential_energy()",
            "system.box_l",
            "part_data(slice(None,None), ['id', 'type'])",
            ]
        system_init_state_request=self.server(request_body,SIDES)
        energy, box_l, part_dict= [
            [result.result()[i] for result in system_init_state_request] 
                for i in range(len(request_body))
                ]

        volume = [float(np.prod(box_l[i])) for i in SIDES]
        
        #save info about particles as pandas.DataFrame
        for side in SIDES:
            for item in part_dict[side]:
                item['side'] = side
        particles_df = pd.concat(pd.DataFrame(part_dict[side]) for side in SIDES)

        #n_mobile = _get_mobile_species_count(particles_df)
        
        new_state = StateData(
            energy = energy, 
            volume = volume, 
            particles_info = particles_df,
        #    n_mobile = n_mobile
            )
        
        self.current_state = new_state
        return new_state
        
    def _choose_random_side_and_part(self):
        side = random.choice(SIDES)
        particles = self.current_state['particles_info']
        rnd_pair_indices = [
            random.choice(particles.query(f'side == {side} & type == {i}')['id'].to_list())
            for i in PAIR
            ]
        return side, rnd_pair_indices

    def move(self) -> Tuple[ReversalData, AcceptCriterion]:
        
        side, pair_indices = self._choose_random_side_and_part()
        other_side = int(not(side))
        
        ###Pair removal:##################################################
        #request to remove pair but store their pos and v
        #request.result will return [[part.id, part.pos, part.v], [part.id, part.pos, part.v]]
        attrs_to_return = {'id':'int', 'pos':'list', 'v':'list'}
        request_body = [
            f"remove_particle({pair_indices[i]},{attrs_to_return})" 
            for i in PAIR]
        remove_part = self.server(request_body,side)
        
        #request to calculate energy after the pair removal, 
        #separated from previous one so we could do something else while executing
        energy_after_removal = self.server("potential_energy()", side)
        
        #rotate velocity vectors
        #can be done when remove_part request is done, 
        removed_pair_velocity = [remove_part.result()[i]['v'] for i in PAIR]
        added_pair_velocity = _rotate_velocities_randomly(removed_pair_velocity)


        ###Pair_addition###################################################
        #request to add pair and return assigned id then to calculate potential energy
        CHARGE = [-1, 1]
        attrs_to_return = {'id':'int'}
        request_body = [
            f"add_particle(attrs_to_return={attrs_to_return}, v={added_pair_velocity[i]}, q = {CHARGE[i]}, type = {i})" 
            for i in PAIR
            ]
        add_part = self.server(request_body, other_side)
        energy_after_addition = self.server("potential_energy()", other_side)

        ###Entropy change#######################################################
        #n1 = self.current_state['n_mobile'][side]
        #n2 = self.current_state['n_mobile'][other_side]
        v0 = self.current_state['volume'][side]
        v1 = self.current_state['volume'][other_side]
        particles_info = self.current_state['particles_info'].groupby(by = ['type', 'side']).size()
        anion0, anion1 = particles_info[0]
        cation0, cation1 = particles_info[1]
        delta_S = _entropy_change(anion0,anion1,cation0,cation1,v0,v1,side)

        ###Energy change###################################################
        #note that 'energy_after_removal' is required only now, 
        #so that the code between the request and 'energy_after_removal.result()'
        #has not been blocked
        new_energy = [None, None]
        new_energy[side] = energy_after_removal.result()
        new_energy[other_side] = energy_after_addition.result()

        ###All the data needed to reverse the move or update state##############
        reversal_data =  ReversalData(
            removed = remove_part.result()[0:2],
            added  = add_part.result()[0:2],
            side = side,
            energy = new_energy)
        
        ###Data to decide whether to accept step################################
        accept_criterion = AcceptCriterion(
            dE = sum(new_energy) - sum(self.current_state['energy']),
            dS = delta_S,
            beta = 1
            )
        #return data that we can reverse or update the system state with
        return reversal_data, accept_criterion
    
    def _particle_info_df_update(self, reversal: ReversalData):
        side = reversal['side']
        other_side = int(not(side))

        
        df = self.current_state['particles_info']
        for i in PAIR:
            _id = reversal['removed'][i]['id']
            df = df.loc[((df['id'] != _id)|(df['side'] != side))]
        
        added = pd.DataFrame(reversal['added'])
        added['side'] = other_side
        added['type'] = [0,1]
        df = df.append(
            added,
            ignore_index=True, verify_integrity=True
            )
        return df

    def update_state(self, reversal: ReversalData):
        part_info = self._particle_info_df_update(reversal)
        update_c_state = StateData(
            energy = reversal['energy'],
            particles_info = part_info,
            #n_mobile = _get_mobile_species_count(part_info)
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

def MC_step_n_mobile_left(MC, n_steps):
    mobile_count = []
    for i in range(n_steps):
        MC.step()
        particle_data = MC.current_state['particles_info'].groupby(by = ['type', 'side']).size()
        mobile_count.append(particle_data[0][0])
    return mobile_count
        
def auto_MC_collect(MC, target_error, initial_sample_size, ci = 0.95, tau = None, timeout = 30):
    start_time = time.time()
    n_samples = initial_sample_size
    x = MC_step_n_mobile_left(MC, n_samples)
    if tau is None: tau = get_tau(x)
    x_mean, x_err = correlated_data_mean_err(x, tau, ci)
    while x_err>target_error:
        elapsed_time = time.time() - start_time
        if elapsed_time > timeout:
            print('Timeout')
            return x_mean, x_err, n_samples
        print(f'Error {x_err} is bigger than target {target_error}')
        print('More data will be collected')
        x=x+MC_step_n_mobile_left(MC, n_samples)
        if tau is None: tau = get_tau(x)
        n_samples = n_samples*2
        x_mean, x_err = correlated_data_mean_err(x, tau, ci)
    else:
        print(f'Mean: {x_mean}, err: {x_err}, eff_sample_size: {n_samples/(2*tau)}')
        return x_mean, x_err, n_samples/(2*tau)