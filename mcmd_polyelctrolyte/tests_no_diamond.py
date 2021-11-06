#%%
from ion_pair_monte_carlo import build_no_gel
from utils import sample_all
import pickle
import pathlib

input_args = dict(
    Volume=[20000,20000], 
    N_pairs=[100,100], 
    A_fixed = 50, 
    log_names=['box_0.log', 'box_1.log'],
    python_executable='pypresso',
    )

MC = build_no_gel(**input_args)
#MC.equilibrate(rounds=5)
result = sample_all(MC, sample_size=5)
result.update({'input':input_args})

output_fname = pathlib.Path(__file__).stem+'.pkl'
output_dir = pathlib.Path(__file__).parent.parent / 'data'
with open(output_dir/output_fname, 'wb') as f:
    pickle.dump(result, f)