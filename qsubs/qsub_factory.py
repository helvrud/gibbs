#%%
def pbs_part(N, mem, ncpus, walltime, prefix):
    return ''.join((
        f'#PBS -N {N}\n',
        f'#PBS -l mem={mem}mb\n',
        f'#PBS -l ncpus={ncpus}\n',
        f'#PBS -l walltime={walltime}\n',
        f'#PBS -m ae\n',
        f'#PBS -e {prefix}/gibbs/data/{N}.qsuberr\n',
        f'#PBS -o {prefix}/gibbs/data/{N}.qsubout\n',
    ))

def singularity_exec(prefix, pypresso_docker, args):
    return ''.join((
        f"singularity exec ",
        f"{prefix}/ubuntu-gibbs.img {pypresso_docker} ",
        f"{prefix}/gibbs/mcmd_polyelctrolyte/no_diamond_template.py ",
        ))+' '.join([str(v) for v in args])

def generate(prefix, pypresso_docker, args, N=None, mem=500, ncpus=3, walltime="1:0:0"):
    if N is None:
        N = '_'.join([str(v) for v in args]).replace('-','')
    with open(f"{N}.qsub", 'w') as f:
        f.write("#!/bin/bash")
        f.write(pbs_part(N, mem, ncpus, walltime, prefix))
        f.write(singularity_exec(prefix, pypresso_docker, args))

# %%
args = ['-c_s', 0.1, '-gel_init_vol', 20000, '-v', 0.5, '-fixed_anions', 50]
generate("/storage/praha1/home/laktionm", "/home/ml/espresso/espresso/es-build/pypresso", args)
# %%
