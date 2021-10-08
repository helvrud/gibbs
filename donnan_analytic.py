def zeta(N_pairs,v,A_fix):
    import numpy as np
    sqrt = np.sqrt
    return v*(N_pairs - (A_fix*(1 - v)**2/2 + N_pairs*v**2 - (1 - v)*sqrt(A_fix**2*(1 - v)**2 + 4*A_fix*N_pairs*v**2 + 4*N_pairs**2*v**2)/2)/(v**2 - (1 - v)**2))/((1 - v)*(A_fix + (A_fix*(1 - v)**2/2 + N_pairs*v**2 - (1 - v)*sqrt(A_fix**2*(1 - v)**2 + 4*A_fix*N_pairs*v**2 + 4*N_pairs**2*v**2)/2)/(v**2 - (1 - v)**2)))
#def zeta(N_pair,v,A_fix):
#    import numpy as np
#    sqrt = np.sqrt
#    return (v - 1)*(A_fix*v**2 - 2*A_fix*v + A_fix + 2*N_pair*v**2 + (v - 1)*sqrt(A_fix**2*v**2 - 2*A_fix**2*v + A_fix**2 + 4*A_fix*N_pair*v**2 + 4*N_pair**2*v**2))/(v*(A_fix*v**2 - 2*A_fix*v + A_fix + 2*N_pair*v**2 - 2*N_pair*(2*v - 1) + (v - 1)*sqrt(A_fix**2*v**2 - 2*A_fix**2*v + A_fix**2 + 4*A_fix*N_pair*v**2 + 4*N_pair**2*v**2)))

