def zeta(N,v,A_fix):
    import numpy as np
    sqrt = np.sqrt
    return (-2*A_fix*v + A_fix + N*v**2 + v*sqrt(-2*A_fix**2*v + A_fix**2 + N**2*v**2) - sqrt(-2*A_fix**2*v + A_fix**2 + N**2*v**2))/(v*(N*v - N + sqrt(-2*A_fix**2*v + A_fix**2 + N**2*v**2)))
#def zeta(N_pair,v,A_fix):
#    import numpy as np
#    sqrt = np.sqrt
#    return (v - 1)*(A_fix*v**2 - 2*A_fix*v + A_fix + 2*N_pair*v**2 + (v - 1)*sqrt(A_fix**2*v**2 - 2*A_fix**2*v + A_fix**2 + 4*A_fix*N_pair*v**2 + 4*N_pair**2*v**2))/(v*(A_fix*v**2 - 2*A_fix*v + A_fix + 2*N_pair*v**2 - 2*N_pair*(2*v - 1) + (v - 1)*sqrt(A_fix**2*v**2 - 2*A_fix**2*v + A_fix**2 + 4*A_fix*N_pair*v**2 + 4*N_pair**2*v**2)))