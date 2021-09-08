def A_gel_func(N, A_fix, v):
    import numpy as np
    sqrt = np.sqrt
    if v != 0.5:
        return (-2*A_fix*v + A_fix + N*v**2 + (v-1)*sqrt(-2*A_fix**2*v + A_fix**2 + N**2*v**2))/(2*(2*v - 1))
    else:
        return (A_fix**2 + N*(-2.0*A_fix + N))/N/4

def zeta(N, A_fix, v):
    import numpy as np
    a_gel = A_gel_func(N, A_fix, v)
    return np.sqrt(a_gel**2-a_gel*A_fix)/a_gel
