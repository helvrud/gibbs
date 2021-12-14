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
#v = np.round(np.arange(0.1, 0.9, 0.01), 4)

#from grand canonical ensemble calculation
'''
pCl	    \cs	    V       box_l   na^{gel}    cl^{gel}    v_5bar
0.40	0.5702	1.7337	32.0	845.7	    365.8
0.82	0.2083	3.1385	39.0	709.0	    229.1       0.26?
1.00	0.1308	3.2607	39.5	617.7	    137.8       0.30
1.30	0.0617	4.2066	43.0	550.9	    70.9        0.27
2.00	0.0111	7.2268	51.5	490.8	    10.8        0.20
2.22	0.0065	7.8768	53.0	484.7	    4.68        0.15
'''
v = np.round(np.arange(0.3, 0.9, 0.01), 3)
timeout_h = 23


for vv in v:
    args = [
        '-v', vv,
        '-n_pairs', 366,
        '-gel_init_vol', 32**3,
        '-fixed_anions', 30*16+8,
        '-MPC', 30,
        '-bl', 1,
        '-timeout_h', timeout_h,
        '-electrostatic',
        '-debug_server'
        ]
    generate(
        prefix = "/storage/brno2/home/laktionm",
        pypresso_docker="pypresso",
        script_name="gibbs/mcmd_polyelctrolyte/diamond_n_pairs.py",
        args = args,
        ncpus=3,
        walltime=f"{timeout_h+1}:00:0"
        )
# %%
