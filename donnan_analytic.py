def zeta(N_pairs,v,A_fix):
    import numpy as np
    sqrt = np.sqrt
    return (-2*A_fix*v + A_fix + N*v**2 + v*sqrt(-2*A_fix**2*v + A_fix**2 + N**2*v**2) - sqrt(-2*A_fix**2*v + A_fix**2 + N**2*v**2))/(v*(N*v - N + sqrt(-2*A_fix**2*v + A_fix**2 + N**2*v**2)))