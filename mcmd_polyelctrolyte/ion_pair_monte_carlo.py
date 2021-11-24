# %%
from typing import Tuple
import numpy as np
import random, os
try:
    from tqdm import trange
except:
    trange = range

from montecarlo import AbstractMonteCarlo
from montecarlo import StateData, ReversalData, AcceptCriterion
from montecarlo import sample_to_target_error

SIDES = [0, 1]
PAIR = [0, 1]
CHARGES = [-1, 1]
MOBILE_SPECIES = [0, 1]


def _rotate_velocities_randomly(velocities):
    from scipy.spatial.transform import Rotation
    try:
        rot = Rotation.random().as_matrix
    except:  # old numpy method
        rot = Rotation.random().as_dcm
    velocities_rotated = [list(rot().dot(velocity)) for velocity in velocities]
    return velocities_rotated


def _entropy_change(anion_0, anion_1, cation_0, cation_1, volume_0, volume_1, removed_from=0):
    if removed_from == 0:
        return np.log((volume_1/volume_0)**2 * (anion_0*cation_0)/((anion_1+1)*(cation_1+1)))
    elif removed_from == 1:
        return _entropy_change(anion_1, anion_0, cation_1, cation_0, volume_1, volume_0, 0)


class MonteCarloPairs(AbstractMonteCarlo):

    def __init__(self, server):
        super().__init__()
        self.server = server
        self.setup()

    def setup(self) -> StateData:
        # request for energy, volume, mobile ions,
        # here we stay agnostic of immobile species
        request_body = [
            "potential_energy()",
            "system.box_l",
            "set(system.part.select(type=0).id)",  # mobile anions type 0
            "set(system.part.select(type=1).id)",  # mobile cations type 1
        ]
        system_init_state_request = self.server(request_body, SIDES)
        energy, box_l, anion_ids, cation_ids = [
            [result.result()[i] for result in system_init_state_request]
            for i in range(len(request_body))
        ]

        volume = [float(np.prod(box_l[i])) for i in SIDES]
        n_anions = list(map(len, anion_ids))  # anions count
        n_cations = list(map(len, cation_ids))  # cations count

        new_state = StateData(
            energy=energy,
            volume=volume,
            anion_ids=anion_ids,  # anion indices
            cation_ids=cation_ids,  # cation indices
            anions=n_anions,  # anions count
            cations=n_cations  # cations count
        )

        self.current_state = new_state
        return new_state

    def move(self) -> Tuple[ReversalData, AcceptCriterion]:
        # select random side
        side = random.choice([0, 1])
        other_side = int(not(side))
        # if there is no particles to be removed - switch sides
        if self.current_state.anions[side] == 0:
            side, other_side = other_side, side
        # get random indices for cation and anion
        pair_ids = [
            random.choice(tuple(self.current_state.anion_ids[side])),
            random.choice(tuple(self.current_state.cation_ids[side])),
        ]

        ###Pair removal:##################################################
        # request to remove pair but store their pos and v
        # request.result will return [[part.id, part.pos, part.v], [part.id, part.pos, part.v]]
        attrs_to_return = {'id': 'int', 'pos': 'list', 'v': 'list'}
        request_body = [
            f"remove_particle({pair_ids[i]},{attrs_to_return})"
            for i in PAIR]
        remove_part = self.server(request_body, side)

        # request to calculate energy after the pair removal,
        # separated from previous one so we could do something else while executing
        energy_after_removal = self.server("potential_energy()", side)

        # rotate velocity vectors
        # can be done when remove_part request is done,
        removed_pair_velocity = [remove_part.result()[i]['v'] for i in PAIR]
        added_pair_velocity = _rotate_velocities_randomly(
            removed_pair_velocity)

        ###Pair_addition###################################################
        # request to add pair and return assigned id then to calculate potential energy
        CHARGE = [-1, 1]
        attrs_to_return = {'id': 'int'}
        request_body = [
            f"add_particle(attrs_to_return={attrs_to_return}, v={added_pair_velocity[i]}, q = {CHARGE[i]}, type = {i})"
            for i in PAIR
        ]
        add_part = self.server(request_body, other_side)
        energy_after_addition = self.server("potential_energy()", other_side)

        ###Entropy change#######################################################
        delta_S = self.entropy_change(side)

        ###Energy change###################################################
        # note that 'energy_after_removal' is required only now,
        # so that the code between the request and 'energy_after_removal.result()'
        # has not been blocked
        new_energy = [None, None]
        new_energy[side] = energy_after_removal.result()
        new_energy[other_side] = energy_after_addition.result()

        ###All the data needed to reverse the move or update state##############
        reversal_data = ReversalData(
            # ids is the first two values in the request result
            removed=remove_part.result()[0:2],
            # ids is the first two values in the request result
            added=add_part.result()[0:2],
            side=side,
            energy=new_energy)

        ###Data to decide whether to accept step################################
        accept_criterion = AcceptCriterion(
            dE=sum(new_energy) - sum(self.current_state['energy']),
            dS=delta_S,
            beta=1
        )
        # return data that we can reverse or update the system state with
        return reversal_data, accept_criterion

    def update_state(self, reversal: ReversalData):
        state = self.current_state
        side = reversal.side
        other_side = int(not(side))
        removed = reversal.removed
        added = reversal.added

        state.anion_ids[side].remove(removed[0]['id'])
        state.cation_ids[side].remove(removed[1]['id'])
        state.anion_ids[other_side].add(added[0]['id'])
        state.cation_ids[other_side].add(added[1]['id'])

        state.anions[side] -= 1
        state.cations[side] -= 1
        state.anions[other_side] += 1
        state.cations[other_side] += 1

        state.energy = reversal.energy

    def reverse(self, reversal_data: ReversalData):
        side = reversal_data.side
        other_side = int(not(side))

        self.server([
            f"add_particle(['id'], q = {CHARGES[i]}, type = {i}, **{reversal_data['removed'][i]})"
            for i in PAIR
        ], side)
        self.server([
            f"remove_particle({reversal_data['added'][i]['id']},['id'])"
            for i in PAIR
        ], other_side)

    # AUXILIARY
    def entropy_change(self, side):
        volume = self.current_state.volume
        anion = self.current_state.anions
        cation = self.current_state.cations
        return _entropy_change(*anion, *cation, *volume, side)

    def zeta(self):
        state = self.current_state
        volume_salt, volume_gel = state.volume
        anion_salt, anion_gel = state.anions
        zeta = float((anion_gel*volume_salt)/(anion_salt*volume_gel))
        return zeta

    # SAMPLING FUNCTIONS
    def sample_zeta_to_target_error(self, **kwargs):
        def get_zeta_callback(sample_size):
            zetas = []
            for i in range(sample_size):
                zeta = self.zeta(self.current_state)
                zetas.append(zeta)
                self.step()
            return np.array(zetas)
        return sample_to_target_error(get_zeta_callback, **kwargs)

    def sample_particle_count_to_target_error(self, **kwargs):
        def get_particle_count_callback(sample_size):
            anions = []
            for i in range(sample_size):
                a = self.current_state.anions[0]
                anions.append(a)
                self.step()
            return np.array(anions)

        anion_salt, eff_err, eff_sample_size = sample_to_target_error(
            get_particle_count_callback, **kwargs)

        cation_salt = anion_salt
        anion_gel = sum(self.current_state.anions) - anion_salt
        cation_gel = sum(self.current_state.cations) - cation_salt

        return {
            'anion': (anion_salt, anion_gel),
            'cation': (cation_salt, cation_gel),
            'zeta' : self.zeta(),
            'err': eff_err,
            'sample_size': eff_sample_size
        }

    def sample_pressures_to_target_error(self, **kwargs):
        request = self.server(
            f'sample_pressure_to_target_error(**{kwargs})', [0, 1])
        pressure_0, err_0, sample_size_0 = request[0].result()
        pressure_1, err_1, sample_size_1 = request[1].result()
        return {
            'pressure': (pressure_0, pressure_1),
            'err': (err_0, err_1),
            'sample_size': (sample_size_0, sample_size_1)
        }

    def sample_Re_to_target_error(self, **kwargs):
        if "initial_sample_size" not in kwargs:
            kwargs["initial_sample_size"] = 1000
        if "target_error" not in kwargs:
            kwargs["target_error"] = 0.1
        request = self.server(
            f'sample_Re_to_target_error(**{kwargs})', 1)  # gel box only
        Re, err, sample_size = request.result()
        return {
            'Re': Re,
            'err': err,
            'sample_size': sample_size
        }
    # MD functions

    def run_md(self, md_steps):
        self.server(f"system.integrator.run({md_steps})", [0, 1])
        self.setup()

    def equilibrate(self, md_steps=100000, mc_steps=200, rounds=25):
        self.run_md(md_steps)
        for ROUND in trange(rounds):
            [self.step() for i in range(mc_steps)]
            self.run_md(md_steps)
        return True

    def populate(self, N_pairs):
        """Populates boxes with ion pairs excl. counterion
        """
        MOBILE_SPECIES_COUNT = [
            {'anion': int(N_pairs[0]), 'cation': int(N_pairs[0])},  # left side
            {'anion': int(N_pairs[1]), 'cation': int(
                N_pairs[1])},  # right side
        ]
        from espresso_nodes.shared import PARTICLE_ATTR
        for i, side in enumerate(MOBILE_SPECIES_COUNT):
            for species, count in side.items():
                print(f'Added {count} of {species}', end=' ')
                print(*[f'{attr}={val}' for attr,
                      val in PARTICLE_ATTR[species].items()], end=' ')
                print(f'to side {i} ')
                self.server(
                    f"populate({count}, **{PARTICLE_ATTR[species]})", i)
        self.setup()
        return True

################################################################################


def build_no_gel(
    Volume, N_pairs, fixed_anions,
    log_names, electrostatic=False,
    no_interaction=False,
    python_executable='python',
    script_name = 'espresso_nodes/run_node.py'
):
    import subprocess
    import socket_nodes


    #HD = HD+'/Studium'
    # box volumes and dimmensions
    box_l = [V_**(1/3) for V_ in Volume]

    # start server and nodes
    server = socket_nodes.utils.create_server_and_nodes(
        scripts=[script_name]*2,
        args_list=[
            [
                '-l', box_l[0], '--salt', "-log_name", log_names[0]
            ]+(['--no_interaction'] if no_interaction else []),
            [
                '-l', box_l[1], '--salt', "-log_name", log_names[1]
            ]+(['--no_interaction'] if no_interaction else []),
        ],
        python_executable=python_executable,
        #stdout=subprocess.PIPE,
        #stderr=subprocess.PIPE,
    )
    # simulate polyelectrolyte without diamond structure
    from espresso_nodes.shared import PARTICLE_ATTR
    # add counterions
    server(f"populate({fixed_anions}, **{PARTICLE_ATTR['cation']})", 1)
    # add fixed anions
    server(f"populate({fixed_anions}, **{PARTICLE_ATTR['gel_anion']})", 1)

    MC = MonteCarloPairs(server)

    MC.populate(N_pairs)

    if electrostatic:
        server('enable_electrostatic()', [0, 1])
        print("Electrostatic is enabled")

    return MC


def build_no_gel_salinity(
    c_s_mol, gel_initial_volume, v, **kwargs
):
    from utils import mol_to_n
    from analytic_donnan import speciation, speciation_inf_reservoir
    c_s = mol_to_n(c_s_mol, unit_length_nm=0.35)
    fixed_anions = kwargs["fixed_anions"]
    anions_inf_res, cations_inf_res = speciation_inf_reservoir(
        c_s, fixed_anions, gel_initial_volume)
    gel_volume = gel_initial_volume*v
    salt_volume = gel_initial_volume*(1-v)
    anion_salt, anion_gel, cation_salt, cation_gel = map(
        round,
        speciation(cations_inf_res, fixed_anions, salt_volume, gel_volume)
    )
    print('Whithin donnan theory:\t',
        f"anion_salt: {anion_salt}",
        f"anion_gel: {anion_gel}",
        f"cation_salt: {cation_salt}",
        f"cation_gel: {cation_gel}")
    MC = build_no_gel(
        Volume=[salt_volume, gel_volume],
        N_pairs=[anion_salt, anion_gel],
        **kwargs)
    return MC
