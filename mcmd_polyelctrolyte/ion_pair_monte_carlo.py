#%%
from typing import Tuple
import numpy as np
import pandas as pd
import random

from montecarlo import AbstractMonteCarlo
from montecarlo import StateData, ReversalData, AcceptCriterion
from montecarlo import sample_to_target_error

SIDES = [0,1]
PAIR = [0,1]
CHARGES=[-1,1]
MOBILE_SPECIES = [0,1]

def _rotate_velocities_randomly(velocities):
    from scipy.spatial.transform import Rotation
    rot = Rotation.random().as_matrix
    velocities_rotated = [list(rot().dot(velocity)) for velocity in velocities]
    return velocities_rotated

def _entropy_change(anion_0, anion_1, cation_0, cation_1, volume_0, volume_1, removed_from = 0):
    if removed_from == 0:
        return np.log((volume_1/volume_0)**2   *   (anion_0*cation_0)/((anion_1+1)*(cation_1+1)))
    elif removed_from == 1:
        return _entropy_change(anion_1, anion_0, cation_1, cation_0, volume_1, volume_0, 0)

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
        particles_df = pd.concat([pd.DataFrame(part_dict[side]) for side in SIDES], ignore_index=True)

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
        volumes = self.current_state['volume']
        particles_info = self.current_state['particles_info'].groupby(by = ['type', 'side']).size()
        anions= particles_info[0]
        cations= particles_info[1]
        delta_S = _entropy_change(*anions,*cations,*volumes, side)

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
        
    def sample_zeta_to_target_error(self, **kwargs):
        def get_zeta_callback(sample_size):
            zetas = []
            for i in range(sample_size):
                zeta = zeta_on_system_state(self.current_state)
                zetas.append(zeta)
                self.step()
            return zetas
        if "initial_sample_size" not in kwargs:
            kwargs["initial_sample_size"] = len(self.current_state['particles_info'])
        if "target_error" not in kwargs:
            kwargs["target_error"] = 0.01
        return sample_to_target_error(get_zeta_callback, **kwargs)

################################################################################
def _zeta(anion_salt, anion_gel, volume_salt, volume_gel):
    return (anion_gel*volume_salt)/(anion_salt*volume_gel)

def zeta_on_system_state(system_state):
    volume_salt, volume_gel = system_state['volume']
    particle_df = system_state['particles_info']
    anion_salt = len(particle_df.loc[(particle_df['type'] == 0)&(particle_df['side'] == 0)])
    anion_gel = len(particle_df.loc[(particle_df['type'] == 0)&(particle_df['side'] == 1)])
    zeta = (anion_gel*volume_salt)/(anion_salt*volume_gel)
    return zeta
        
