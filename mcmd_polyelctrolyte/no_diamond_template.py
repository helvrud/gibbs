"""
Template script to call MCMD to sample particles count and pressures
Change input_args and script name for the task
Set n_steps, rounds, timeouts, etc. to low values for debugging

Pickled results will be saved to ../data/script_name.pkl

@author: Mikhail Laktionov
"""
from ion_pair_monte_carlo import build_no_gel
from utils import sample_all
import pickle
import pathlib

import os
import sys
#os.chdir(os.path.dirname(sys.argv[0]))
#print(pwd())
##INPUT##
input_args = dict(
    
    Volume=[20000,20000], 
    N_pairs=[100,100], 
    fixed_anions = 50, 
    log_names=['box_0.log', 'box_1.log'],
    python_executable='/home/kvint/espresso/es-build/pypresso',
    
    )

#build monte carlo class instance, with no gel created, only salt reservoirs
MC = build_no_gel(**input_args)

#equilibration steps
MC.equilibrate(
    rounds=3, #repeats mc and md steps, 10 rounds seems to be enough,
    md_steps=100000, #call integrator.run(md_steps)
    mc_steps=sum(input_args['N_pairs']) #the same as pairs count
    )

#sample number of particles of each mobile species and pressures in the boxes
#by alternating number of particles sampling and pressure sampling routines
result = sample_all(
    MC,
    sample_size=5, #number of samples   #|--------------------------------------
    n_particle_sampling_kwargs = dict(  #| n_particle sampling routine settings
        timeout = 10,                   #| omit or comment out to use defaults
        initial_sample_size = 10        #| set target_error, timeout, 
        ),                              #| initial_sample_size kwarg here
                                        #|--------------------------------------
    pressure_sampling_kwargs=dict(      #| pressures sampling routine settings
        timeout = 10,                   #| see comment above
        initial_sample_size = 10        #| set short timeout and  
        )                               #| small initial_sample_size for debug
    )                                   #|--------------------------------------

#add inputs to output file and save the pickle to ../data/script_name.pkl
result.update({'input':input_args})
print(result)

output_fname = pathlib.Path(__file__).stem+'.pkl'
output_dir = pathlib.Path(__file__).parent.parent / 'data'
with open(output_dir/output_fname, 'wb') as f:
    pickle.dump(result, f)
