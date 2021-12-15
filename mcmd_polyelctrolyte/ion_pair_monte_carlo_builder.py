from ion_pair_monte_carlo import MonteCarloPairs
import socket_nodes
import logging
logger = logging.getLogger(__name__)

def build_no_gel(
    Volume, N_pairs, fixed_anions,
    electrostatic=False,
    no_interaction=False,
    python_executable='python',
    script_name = 'espresso_nodes/run_node.py',
    args=[[],[]]
):
    import socket_nodes

    # box volumes and dimmensions
    box_l = [V_**(1/3) for V_ in Volume]

    # start server and nodes
    server = socket_nodes.utils.create_server_and_nodes(
        scripts=[script_name]*2,
        args_list=[
            [
                '-l', box_l[0], '--salt',
            ]+(['--no_interaction'] if no_interaction else []) + args[0],
            [
                '-l', box_l[1], '--salt',
            ]+(['--no_interaction'] if no_interaction else []) + args[1],
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

    server("minimize_energy()", [0,1])

    if electrostatic:
        logger.info("Enabling electrostatic...")
        server('enable_electrostatic()', [0, 1])
        logger.info("Electrostatic is enabled")

    return MC

def build_gel(
    Volume : tuple,
    N_pairs : tuple,
    fixed_anions : int,
    MPC : int,
    bond_length : float,
    electrostatic : bool = False,
    no_interaction : bool = False,
    python_executable = 'python',
    script_name = 'espresso_nodes/run_node.py',
    args=[[],[]]
):

    n_gel_part = MPC*16+8
    # box volumes and dimmensions
    box_l = [V_**(1/3) for V_ in Volume]

    # start server and nodes
    server = socket_nodes.utils.create_server_and_nodes(
        scripts=[script_name]*2,
        args_list=[
            [
                '-l', box_l[0], '--salt',
            ]+(['--no_interaction'] if no_interaction else []) + args[0],
            [
                '-l', box_l[1], '--gel', '-MPC', MPC,
                '-bond_length', bond_length, '-alpha', fixed_anions/n_gel_part
            ]+(['--no_interaction'] if no_interaction else []) + args[1],
        ],
        python_executable=python_executable,
        connection_timeout_s = 2400
        #stdout=subprocess.PIPE,
        #stderr=subprocess.PIPE,
    )

    MC = MonteCarloPairs(server)
    MC.populate(N_pairs)
    server("minimize_energy()", [0,1])

    if electrostatic:
        logger.info("Enabling electrostatic...")
        server('enable_electrostatic()', [0, 1])
        server.wait_all_nodes()
        logger.info("Electrostatic is enabled")

    return MC

def build_gel_salinity(
    c_s_mol, gel_initial_volume, v, **kwargs
):
    from utils import mol_to_n
    from analytic_donnan import speciation, speciation_inf_reservoir
    #particles per sigma^3
    c_s = mol_to_n(c_s_mol, unit_length_nm=0.35)
    fixed_anions = kwargs["fixed_anions"]
    #'soak' gel in inf reservoir
    anions_inf_res = round(speciation_inf_reservoir(
        c_s, fixed_anions, gel_initial_volume)[0])

    gel_volume = gel_initial_volume*v
    salt_volume = gel_initial_volume*(1-v)

    anion_salt, anion_gel, cation_salt, cation_gel = map(
        round,
        speciation(anions_inf_res, fixed_anions, salt_volume, gel_volume)
    )
    print('Whithin donnan theory:\t',
        f"anion_salt: {anion_salt}",
        f"anion_gel: {anion_gel}",
        f"cation_salt: {cation_salt}",
        f"cation_gel: {cation_gel}")
    MC = build_gel(
        Volume=[salt_volume, gel_volume],
        N_pairs=[anion_salt, anion_gel],
        **kwargs)
    return MC

def build_gel_n_pairs(
    n_pairs_all : float,
    gel_initial_volume : float,
    v : float,
    **kwargs
    ):
    from analytic_donnan import speciation
    fixed_anions = kwargs["fixed_anions"]
    gel_volume = gel_initial_volume*v
    salt_volume = gel_initial_volume*(1-v)
    anion_salt, anion_gel, cation_salt, cation_gel = map(
        round,
        speciation(n_pairs_all, fixed_anions, salt_volume, gel_volume)
    )
    print(f'Started with {n_pairs_all} pairs')
    print('Whithin donnan theory:\t',
        f"anion_salt: {anion_salt}",
        f"anion_gel: {anion_gel}",
        f"cation_salt: {cation_salt}",
        f"cation_gel: {cation_gel}")
    MC = build_gel(
        Volume=[salt_volume, gel_volume],
        N_pairs=[anion_salt, anion_gel],
        **kwargs)
    return MC