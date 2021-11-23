#%%
from ion_pair_monte_carlo import build_no_gel, build_no_gel_salinity
from utils import sample_all
from analytic_donnan import speciation_inf_reservoir, speciation
import pickle
import pathlib

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

logs_dir = file_dir / 'logs'
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


##CLI INPUT##
import argparse
parser = argparse.ArgumentParser(description="...")
parser.add_argument('-c_s', action='store', type = float)
parser.add_argument('-gel_init_vol', action='store', type = float)
parser.add_argument('-v', action='store', type = float)
parser.add_argument('-fixed_anions', action='store', type = int)
#try:
args = parser.parse_args()
input_args = dict(
    gel_initial_volume = args.gel_init_vol,
    c_s_mol = args.c_s,
    fixed_anions = args.fixed_anions,
    log_names=log_names,
    no_interaction=False,
    python_executable=python_executable,
    script_name = run_node_path,
    v = args.v
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
    rounds=10,  # repeats mc and md steps, 10 rounds seems to be enough,
    md_steps=100000,  # call integrator.run(md_steps)
)
#%%
# sample number of particles of each mobile species and pressures in the boxes
# by alternating number of particles sampling and pressure sampling routines
result = sample_all(
    MC,
    sample_size=20, # number of samples # |--------------------------------------
    n_particle_sampling_kwargs=dict(    # | n_particle sampling routine settings
        timeout=60,                     # |
        target_error = 0.1,             # | omit or comment out to use defaults
        initial_sample_size=100         # | set target_error, timeout,
    ),                                  # | initial_sample_size kwarg here
                                        # |--------------------------------------
    pressure_sampling_kwargs=dict(      # | pressures sampling routine settings
        timeout=60,                     # |
        target_error = 0.01,            # | see comment above
        initial_sample_size=100         # | set short timeout and
    )                                   # | small initial_sample_size for debug
)                                       # |--------------------------------------

# add inputs to output file and save the pickle to ../data/script_name.pkl
result.update({'input':input_args})
print(result)

with open(output_dir/output_fname, 'wb') as f:
    pickle.dump(result, f)

print ("DONE")