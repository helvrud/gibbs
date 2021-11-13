# %%
from ion_pair_monte_carlo import build_no_gel, build_no_gel_salinity
from utils import sample_all
from utils import mol_to_n
from analytic_donnan import speciation_inf_reservoir, speciation
import pickle
import pathlib

import os
import sys
os.chdir(os.path.dirname(sys.argv[0]))

#%%
##CLI INPUT##
import argparse
parser = argparse.ArgumentParser(description="...")
parser.add_argument('-c_s', action='store')
parser.add_argument('-gel_init_vol', action='store')
parser.add_argument('-v', action='store')
parser.add_argument('-fixed_anions', action='store')
try:
    args = parser.parse_args()
    input_args = dict(
        gel_initial_volume = parser.gel_init_vol,
        c_s_mol = parser.c_s,
        fixed_anions = parser.fixed_anions, 
        log_names=['', ''],
        python_executable='pypresso',
        v = parser.v
        )
except:
    ##NON-CLI INPUT##
    input_args = dict(
        gel_initial_volume = 20000,
        c_s_mol = 0.1,
        fixed_anions = 50, 
        log_names=['box_0.log', 'box_1.log'],
        python_executable='pypresso',
        v = 0.4
        )

MC = build_no_gel_salinity(**input_args)
# equilibration steps
MC.equilibrate(
    rounds=3,  # repeats mc and md steps, 10 rounds seems to be enough,
    md_steps=100000,  # call integrator.run(md_steps)
)
# sample number of particles of each mobile species and pressures in the boxes
# by alternating number of particles sampling and pressure sampling routines
result = sample_all(
    MC,
    sample_size=5,  # number of samples # |--------------------------------------
    n_particle_sampling_kwargs=dict(    # | n_particle sampling routine settings
        timeout=10,                     # | omit or comment out to use defaults
        initial_sample_size=10          # | set target_error, timeout,
    ),                                  # | initial_sample_size kwarg here
                                        # |--------------------------------------
    pressure_sampling_kwargs=dict(      # | pressures sampling routine settings
        timeout=10,                     # | see comment above
        initial_sample_size=10          # | set short timeout and
    )                                   # | small initial_sample_size for debug
)                                       # |--------------------------------------

# add inputs to output file and save the pickle to ../data/script_name.pkl
result.update({'input':input_args})
print(result)

output_fname = pathlib.Path(__file__).stem+'.pkl'
output_dir = pathlib.Path(__file__).parent.parent / 'data'
with open(output_dir/output_fname, 'wb') as f:
    pickle.dump(result, f)