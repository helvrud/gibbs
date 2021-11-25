#%%
from ion_pair_monte_carlo import build_no_gel, build_no_gel_salinity
from utils import sample_all
from analytic_donnan import speciation_inf_reservoir, speciation
import pickle
import pathlib
import logging

import os
import sys

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
base_name = uuid.uuid4().hex[:8]
output_fname =base_name+'.pkl'
print('output filename', output_fname)
log_names = [
    logs_dir / (base_name+'_salt.log'),
    logs_dir / (base_name+'_gel.log')
    ]
server_log = logs_dir / (base_name+'_server.log')

logging.getLogger("socket_nodes.libserver")
logging.basicConfig(
    level=logging.INFO,
    stream=open(server_log, 'w'),
    format = '%(asctime)s - %(message)s')


##CLI INPUT##
import argparse
parser = argparse.ArgumentParser(description="...")
parser.add_argument('-c_s', action='store', type = float)
parser.add_argument('-gel_init_vol', action='store', type = float)
parser.add_argument('-v', action='store', type = float)
parser.add_argument('-fixed_anions', action='store', type = int),
parser.add_argument('-electrostatic', action = 'store', type = bool, required=False, default=False)
parser.add_argument('-debug_node', action = 'store', type = bool, required=False, default=False)
args = parser.parse_args()
if args.debug_node:
    print('set not to log the nodes')
    other_args =  [
        ['-log_name' , log_names[0]],
        ['-log_name' , log_names[1]]
    ]
else:
    print('set to log the nodes for DEBUG')
    other_args = [[],[]]
input_args = dict(
    gel_initial_volume = args.gel_init_vol,
    c_s_mol = args.c_s,
    fixed_anions = args.fixed_anions,
    no_interaction=False,
    python_executable=python_executable,
    script_name = run_node_path,
    v = args.v,
    electrostatic = args.electrostatic,
    args = other_args
    )
#except:
#    ##NON-CLI INPUT##
#    input_args = dict(
#        gel_initial_volume = 20000,
#        c_s_mol = 0.1,
#        fixed_anions = 50,
#        log_names=log_names,
#        no_interaction=False,
#        python_executable=python_executable,
#        script_name = run_node_path,
#        v = 0.6
#        )

MC = build_no_gel_salinity(**input_args)
#%%
# equilibration steps
MC.equilibrate(
    rounds=25,  # repeats mc and md steps, 10 rounds seems to be enough,
    md_steps=100000,  # call integrator.run(md_steps)
    mc_steps=200
)
#%%
# sample number of particles of each mobile species and pressures in the boxes
# by alternating number of particles sampling and pressure sampling routines

subsampling_params = dict(
    sample_size=200,# number of samples
    n_particle_sampling_kwargs=dict(
        timeout=120,
        target_eff_sample_size = 50,
        initial_sample_size=100
    ),
    pressure_sampling_kwargs=dict(
        timeout=120,
        target_eff_sample_size = 50,
        initial_sample_size=100
    )
)

result = sample_all(
    MC,
    **subsampling_params
)

# add inputs to output file and save the pickle to ../data/script_name.pkl
result.update({'input':input_args})
result.update(subsampling_params)
print(result)

with open(output_dir/output_fname, 'wb') as f:
    pickle.dump(result, f)

print ("DONE")