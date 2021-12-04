from ion_pair_monte_carlo import build_gel, build_gel_n_pairs, build_gel_salinity
from utils import sample_all
import pickle
import pathlib
import logging

import time
start_time = time.time()

##CLI INPUT##
import argparse
parser = argparse.ArgumentParser(description="...")
parser.add_argument('-n_pairs', metavar = 'n_pairs', type = int)
parser.add_argument('-gel_init_vol', metavar = 'gel_init_vol', type = float)
parser.add_argument('-v', metavar = 'v', type = float)
parser.add_argument('-fixed_anions', metavar='fixed_anions', type = int),
parser.add_argument('-MPC', metavar='MPC', type = int),
parser.add_argument('-bl', metavar='bl', type = int),
parser.add_argument('-electrostatic', action = 'store_true', required=False, default=False)
parser.add_argument('-debug_node', action = 'store_true', required=False, default=False)
parser.add_argument('-debug_server', action = 'store_true', required=False, default=False)
parser.add_argument('-timeout_h', metavar='timeout_h', type = float, required=False, default=10.0)

args = parser.parse_args()
print(args)

file_dir =  pathlib.Path(__file__).parent
print('file_dir:', file_dir)

output_dir = file_dir.parent / 'data' / pathlib.Path(__file__).stem
output_dir.mkdir(parents=True, exist_ok=True)

run_node_path = file_dir / 'espresso_nodes'/ 'run_node.py'
print('node script path:', run_node_path)

python_executable = 'pypresso'
print('python executable path', python_executable)

logs_dir = file_dir.parent / 'logs' / pathlib.Path(__file__).stem
logs_dir.mkdir(parents=True, exist_ok=True)
print('path to logs', logs_dir)

#random file name
import uuid
base_name = '{:.4f}'.format(args.v)+'_'+uuid.uuid4().hex[:8]
output_fname =base_name+'.pkl'
print('output filename', output_fname)
log_names = [
    logs_dir / (base_name+'_salt.log'),
    logs_dir / (base_name+'_gel.log')
    ]
server_log = logs_dir / (base_name+'_server.log')

TIMEOUT_H = args.timeout_h
if args.debug_node:
    print('set to log the nodes for DEBUG')
    other_args =  [
        ['-log_name' , log_names[0]],
        ['-log_name' , log_names[1]]
    ]
else:
    print('set not to log the nodes')
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

MC = build_gel_n_pairs(**input_args)
# equilibration steps
MC.equilibrate(
    rounds=25,  # repeats mc and md steps, 10 rounds seems to be enough,
    md_steps=10000,  # call integrator.run(md_steps)
    mc_steps=200,
    timeout_h=1 #let's not spend to much time on it :)
)

# sample number of particles of each mobile species and pressures in the boxes
# by alternating number of particles sampling and pressure sampling routines
print("Hours left for sampling", TIMEOUT_H-(time.time() - start_time)/3600)
subsampling_params = dict(
    target_sample_size=200,# number of samples,
    timeout = TIMEOUT_H*3600 - (time.time() - start_time),
    n_particle_sampling_kwargs=dict(
        timeout=120,
        target_eff_sample_size = 100,
        initial_sample_size=100
    ),
    pressure_sampling_kwargs=dict(
        timeout=120,
        target_eff_sample_size = 50,
        initial_sample_size=100
    )
)

#save sampling settings to output
result = sample_all(
    MC,
    **subsampling_params
)

# add inputs to output file and save the pickle to ../data/script_name.pkl
result.update({'input':input_args})
result.update(subsampling_params)
result.update({"timeout_h" : TIMEOUT_H})
print(result)

with open(output_dir/output_fname, 'wb') as f:
    pickle.dump(result, f)

print("DONE")