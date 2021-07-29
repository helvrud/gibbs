from typing import Tuple
class ReversalData(dict):
    pass

class StateData(dict):
    pass

class AcceptCriterion(dict):
    pass

class AbstractMonteCarlo:
    current_state : StateData
    def __init__(self):
        pass
    
    def setup(self) -> StateData:
        pass

    def move(self) -> Tuple[ReversalData, AcceptCriterion]:
        pass

    def reverse(self, reverse_data : ReversalData):
        pass

    def accept(self, criterion: AcceptCriterion) -> bool:
        dE = criterion['dE']
        dS = criterion['dS']
        beta = criterion['beta']
        dF = dE-dS
        if dF<0:
            return True
        else:
            prob = math.exp(-beta*dF)
            return (prob > random.random())

    def on_accept(self):
        pass

    def on_reject(self):
        pass

    def update_state(self, reversal : ReversalData):
        pass

    def step(self):
        reversal, accept_criterion = self.move()
        if self.accept(accept_criterion):
            self.update_state(reversal)
            self.on_accept()
        else:
            self.reverse(reversal)
            self.on_reject()
        return self.current_state

import numpy as np
import pandas as pd
import math
import random
SIDES = [0,1]
PAIR = [0,1]
CHARGES=[-1,1]
def _rotate_velocities_randomly(velocities):
    from scipy.spatial.transform import Rotation
    rot = Rotation.random().as_matrix
    velocities_rotated = [list(rot().dot(velocity)) for velocity in velocities]
    return velocities_rotated
def _entropy_change(N1, N2, V1, V2, n=1):
    #N1, V1 - box we removing particle from
    #N2, V2 - box we adding to
    #n - number of particles 
    if n==1:
        return math.log((N1*V2)/((N2+1)*V1))
    elif n==2:
        return math.log((V2/V1)**2*(N1*(N1-1))/((N2+2)*(N2+1)))
from typing import Tuple

class MonteCarloSocketNodes(AbstractMonteCarlo):
    def __init__(self, server):
        super().__init__()
        self.server = server
        self.current_state = self.setup()

    def setup(self) -> StateData:
        self.steps = 0
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
        
        for i,dict_ in enumerate(part_dict):
            dict_['side'] = i

        #save info about particles as pandas.DataFrame
        particles_df = pd.concat([
            pd.DataFrame(dict_) for dict_ in part_dict
            ], ignore_index=True)

        #n_particles = self.particles.groupby(by=['side', 'type']).size()
        #mobile_particles_n
        n_mobile = particles_df.loc[particles_df.type!=2].groupby(by='side').size().to_list()
        new_state = StateData(
            energy = energy, 
            volume = volume, 
            particles_info = particles_df,
            n_mobile = n_mobile)

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
        request_body = [
            f"add_particle(attrs_to_return=['id'], v={added_pair_velocity[i]}, q = {CHARGE[i]}, type = {i})" 
            for i in PAIR
            ]
        add_part = self.server(request_body, other_side)
        energy_after_addition = self.server("potential_energy()", other_side)

        ###Entropy change#######################################################
        n1 = self.current_state['n_mobile'][side]
        n2 = self.current_state['n_mobile'][other_side]
        v1 = self.current_state['volume'][side]
        v2 = self.current_state['volume'][other_side]
        delta_S = _entropy_change(n1,n2,v1,v2,2)

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
            n_mobile = part_info.loc[part_info.type!=2].groupby(by='side').size().to_list()
        )
        self.current_state.update(update_c_state)

    def reverse(self, reversal_data: ReversalData):
        side = reversal_data['side']
        other_side = int(not(side))
        reverse_remove = self.server([
            f"add_particle(['id'], q = {CHARGES[i]}, type = {i}, **{reversal_data['removed'][i]})"
            for i in PAIR
            ], side)
        
        reverse_add = self.server([
            f"remove_particle({reversal_data['added'][i]['id']},['id'])" 
            for i in PAIR
            ], other_side)