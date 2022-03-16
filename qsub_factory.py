#%%
def pbs_part(N, mem, ncpus, walltime, prefix):
    return ''.join((
        f'#PBS -N {N}\n',
        f'#PBS -l mem={mem}mb\n',
        f'#PBS -l ncpus={ncpus}\n',
        f'#PBS -l walltime={walltime}\n',
        f'#PBS -m ae\n',
        f'#PBS -e {prefix}/gibbs/qsuberr/{N}.qsuberr\n',
        f'#PBS -o {prefix}/gibbs/qsubout/{N}.qsubout\n',
    ))

def singularity_exec(prefix, pypresso_docker, script_name, args):
    return ''.join((
        f"singularity exec ",
        f"{prefix}/ubuntu-gibbs.img {pypresso_docker} ",
        f"{prefix}/{script_name} ",
        ))+' '.join([str(v) for v in args])

def generate(prefix, pypresso_docker, script_name, args, N=None, mem=500, ncpus=1, walltime="24:00:0"):
    import pathlib
    if N is None:
        N = '_'.join([str(v) for v in args]).replace('-','')
    output_dir = pathlib.Path(__file__).parent/ 'qsubs'
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir/f"{N}.qsub", 'w') as f:
        f.write("#!/bin/bash\n")
        f.write(pbs_part(N, mem, ncpus, walltime, prefix))
        f.write("\n")
        f.write(singularity_exec(prefix, pypresso_docker, script_name, args))

import numpy as np
v = np.round(np.arange(0.3, 0.9, 0.01), 3) # ratio of the gel volume to the total volume
timeout_h = 96


for vv in v:
    args = [
        '-v', vv,
        '-n_pairs', 86, 
        '-gel_init_vol', 42**3, # espresso units, sigma
        '-fixed_anions', 30*16+8,
        '-MPC', 30,
<<<<<<< HEAD
        '-bl', 1, # bond length
=======
        '-bl', 1, # bond_length
>>>>>>> 9a6ff7ec166d6506fe5bdd74ecfbc34d1c40c703
        '-timeout_h', timeout_h,
        '-electrostatic', # True, False
        '-debug_server' # Will log info from server
        ]
    generate(
        prefix = "/storage/brno2/home/kvint",
        pypresso_docker="pypresso",
        script_name="gibbs/mcmd_polyelctrolyte/diamond_n_pairs.py",
        args = args,
        ncpus=3,
        walltime=f"{timeout_h+1}:00:0"
        )
# %%
