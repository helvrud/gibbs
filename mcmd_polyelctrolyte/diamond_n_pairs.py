import logging
import pathlib
import time
import uuid

from ion_pair_monte_carlo_builder import build_gel_n_pairs
from sample_pressure_and_particles import sample_all
logger = logging.getLogger(__name__)

start_time = time.time()

##CLI INPUT##
#example
#python  mcmd_polyelctrolyte/diamond_n_pairs.py -gel_init_vol 50000 -n_pairs 100 -v 0.6 -fixed_anions 488 -MPC 30 -bl 1 -debug_node -debug_server -timeout_h 0.4
import argparse

parser = argparse.ArgumentParser(description="...")
parser.add_argument('-n_pairs', metavar = 'n_pairs', type = int)
parser.add_argument('-gel_init_vol', metavar = 'gel_init_vol', type = float)
parser.add_argument('-v', metavar = 'v', type = float)
parser.add_argument('-fixed_anions', metavar='fixed_anions', type = int),
parser.add_argument('-MPC', metavar='MPC', type = int, default=30),
parser.add_argument('-bl', metavar='bl', type = float, default=1.0), # bond length
parser.add_argument('-electrostatic', action = 'store_true', required=False, default=False)
parser.add_argument('-debug_node', action = 'store_true', required=False, default=False)
parser.add_argument('-debug_server', action = 'store_true', required=False, default=False)
parser.add_argument('-timeout_h', metavar='timeout_h', type = float, required=False, default=10.0)
parser.add_argument('-silent', action = 'store_true', required=False, default=False)

args = parser.parse_args()

if args.silent:
    Print = logger.info
else:
    Print = print


Print(args)

file_dir =  pathlib.Path(__file__).parent
Print('file_dir:', file_dir)

output_dir = file_dir.parent / 'data' / pathlib.Path(__file__).stem

.mkdir(parents=True, exist_ok=True)

run_node_path = file_dir / 'espresso_nodes'/ 'run_node.py'
Print('node script path:', run_node_path)

python_executable = 'pypresso'
Print('python executable path', python_executable)

logs_dir = file_dir.parent / 'logs' / pathlib.Path(__file__).stem
logs_dir.mkdir(parents=True, exist_ok=True)
Print('path to logs', logs_dir)

#random file name
base_name = '{:.4f}'.format(args.v)+'_'+uuid.uuid4().hex[:8]
output_fname =base_name+'.pkl'
Print('output filename', output_fname)
log_names = [
    logs_dir / (base_name+'_salt.log'),
    logs_dir / (base_name+'_gel.log')
    ]
server_log = logs_dir / (base_name+'_server.log')

TIMEOUT_H = args.timeout_h
if args.debug_node:
    Print('set to log the nodes for DEBUG')
    other_args =  [
        ['-log_name' , log_names[0]],
        ['-log_name' , log_names[1]]
    ]
else:
    Print('set not to log the nodes')
    other_args = [[],[]]

if args.debug_server:
    logging.getLogger("socket_nodes.libserver")
    logging.basicConfig(
        level=logging.INFO,
        stream=open(server_log, 'w'),
        format = '%(asctime)s - %(message)s')

input_args = dict(
    gel_initial_volume = args.gel_init_vol,
    n_pairs_all = args.n_pairs,
    fixed_anions = args.fixed_anions,
    no_interaction=False,
    python_executable=python_executable,
    script_name = run_node_path,
    v = args.v,
    MPC = args.MPC,
    electrostatic = args.electrostatic,
    bond_length =args.bl,
    args = other_args
    )

equilibration_params = dict(
    rounds=25,  # repeats mc and md steps, 10 rounds seems to be enough,
    md_steps=10000,  # call integrator.run(md_steps)
    mc_steps=args.n_pairs+args.MPC*16,
    timeout_h=1 #let's not spend to much time on it :)
)

subsampling_params = dict(
    target_sample_size=200,# number of samples,
    timeout = TIMEOUT_H*3600 - (time.time() - start_time),
    save_file_path = output_dir/output_fname,
    particle_count_sampling_kwargs=dict(
        timeout=240,
        target_eff_sample_size = 100,
        initial_sample_size=100
    ),
    pressure_sampling_kwargs=dict(
        timeout=240,
        target_eff_sample_size = 50,
        initial_sample_size=100
    )
)

MC = build_gel_n_pairs(**input_args)
# equilibration steps
MC.equilibrate(**equilibration_params)
# sample number of particles of each mobile species and pressures in the boxes
# by alternating number of particles sampling and pressure sampling routines
Print("Hours left for sampling", TIMEOUT_H-(time.time() - start_time)/3600)

# add inputs to output file and save the pickle to ../data/script_name.pkl
result_header = {}
result_header.update({'input':input_args})
result_header.update({"timeout_h" : TIMEOUT_H})


#save sampling settings to output
result = sample_all(
    MC,
    save_file_header = result_header,
    **subsampling_params
)

Print(result)
Print("DONE")
