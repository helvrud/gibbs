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

def generate(prefix, pypresso_docker, script_name, args, N=None, mem=500, ncpus=1, walltime="10:30:0"):
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
v = np.round(np.linspace(0.3, 0.8, 101), 2)

for vv in v:
    args = [
        '-v', vv,
        '-c_s', 0.1,
        '-gel_init_vol', 20000,
        '-fixed_anions', 50,
        '-electrostatic', True
        ]
    generate(
        prefix = "/storage/brno2/home/laktionm",
        #pypresso_docker="/home/ml/espresso/espresso/es-build/pypresso",
        pypresso_docker="pypresso",
        script_name="gibbs/mcmd_polyelctrolyte/no_diamond_conc_as_arg.py",
        args = args,
        ncpus=3
        )

#scp -r qsubs/ laktionm@skirit.metacentrum.cz:gibbs/