#%%
"""
Here we define abstract Monte Carlo class to use as a template to build
a concrete realization of Monte Carlo scheme.

An essential part is AbstractMonteCarlo.step() method that allows us to
explore phase space of a system, when the accept criterion is defined.

To construct a concrete realization one has to provide the next definition:

    ReversalData - dict-like object with the all information needed
        to reverse the move
    StateData - dict-like object with the system parameters we
        want to track
    AcceptCriterion - dict-like object used to calculate whether the move
        be accepted and StateData be updated or the move be rejected

    move(self) -> Tuple[ReversalData, AcceptCriterion]
        an algorithm to calculate ReversalData and AcceptCriterion

@author Mikhail Laktionov
"""
from typing import Tuple
class ReversalData(dict):
    """
    A dict-like object holds the data for reversing Monte-Carlo move
    """
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

class StateData(dict):
    """
    A dict-like object holds the data to track system parameters
    """
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

class AcceptCriterion(dict):
    """
    A dict-like object holds the data to decide whether to accept or reject the
    move
    """
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

class AbstractMonteCarlo:
    """
    An abstract definition of Monte-Carlo Metropolis-Hastings algorithm
    agnostic to studied system
    """
    current_state : StateData
    def __init__(self):
        pass

    def setup(self) -> StateData:
        """The method should be used to get the system parameters right after
        initialization or when some changes happened that are not caused by the
        class methods and thus untracked.

        Returns:
            StateData: current system parameters
        """
        pass

    def move(self) -> Tuple[ReversalData, AcceptCriterion]:
        """Abstract method to calculate the next state of the system,
        assure you return ReversalData to be able to reverse the move if
        rejected and AcceptCriterion to decide whether the move be accepted.

        Note that you should not implement any self.current_state updates here.

        Returns:
            Tuple[ReversalData, AcceptCriterion]:
        """
        pass

    def reverse(self, reverse_data : ReversalData):
        """A procedure to reverse self.move() method with the data provided
        reverse_data

        Args:
            reverse_data (ReversalData): dict-like object with
            the all information needed to reverse the move
        """
        pass

    def accept(self, criterion: AcceptCriterion) -> bool:
        """Here we decide whether the proposal be rejected or accepted.
        Default implementation assumes you know change in potential energy
        and entropy so it uses change in free energy for the decision.
        If the change in free energy is negative the move is accepted, otherwise
        it is accepted with some probability. Rejection/acception rate is also
        controlled by the factor beta (in most cases beta = 1/kT).

        Args:
            criterion (AcceptCriterion): dict-like object to calculate the
                criterion
        Returns:
            bool: True if accepted, False otherwise
        """
        import random
        import math
        dE = criterion['dE']
        dS = criterion['dS']
        beta = criterion['beta']
        dF = dE-dS
        if dF<0:
            return True
        else:
            prob = math.exp(-beta*dF)
            return (prob > random.random())

    def on_accept(self):
        """
        Routines to do after the acception, appart from system state updating
        """
        pass

    def on_reject(self):
        """
        Routines to do after the rejection
        """
        pass

    def update_state(self, reversal : ReversalData):
        """The routine to update

        Args:
            reversal (ReversalData): [description]
        """
        pass

    def step(self):
        """
        The method is used for equilibration or sampling of the system,
        most likely you can leave it without any changes.

        Returns:
            [StateData]: system state after the step is made
        """
        reversal, accept_criterion = self.move()
        if self.accept(accept_criterion):
            self.update_state(reversal)
            self.on_accept()
        else:
            self.reverse(reversal)
            self.on_reject()
        return self.current_state

#####Related statistics#########################################################
#Will be moved to separate package!!!!
def get_tau(x, acf_n_lags : int = 200):
    """Get the integrated autocorrelation time i.e. the distance between measurements
    when the data can be considered uncorrelated.

    Args:
        x (array): array of consecutive measurements
        acf_n_lags (int, optional): Number of lags calculated with ACF. Defaults to 200.

    Returns:
        float: integrated autocorrelation time
    """
    #acf - autocorrelation function
    from statsmodels.tsa.stattools import acf
    import numpy as np
    acf_arr = acf(x, nlags = acf_n_lags)
    #integrated autocorrelation time
    tau_int =1/2+max(np.cumsum(acf_arr))
    return tau_int

def correlated_data_mean_err(x, tau, ci = 0.95):
    """Returns the mean and the confidence interval of correlated sample.
    That distribution mean lies in sample mean +/- error with a probability of
    conference interval level (95% in most cases).
    Error = z * standard error of the sample

    Margins of the error calculated from standard error of a sample with
    inverse cumulative normal distribution (z-values) if the sample size is big
    (30+) or with a inverse cumulative t-distribution (t-values) for a small
    sample.

    Args:
        x (array): correlated sample
        tau (float): integrated autocorrelation time
        ci (float, optional): Confidence interval level. Defaults to 0.95.

    Returns:
        (float, float): sample mean and the margin of error
    """
    ##References:
    #http://www.stat.yale.edu/Courses/1997-98/101/confint.html
    #https://en.wikipedia.org/wiki/Confidence_interval
    import scipy.stats
    import numpy as np
    x_mean = np.mean(x)

    #the sample is correlated so the effective size is smaller
    n_eff = np.size(x)/(2*tau)
    #print(f"Effective sample size: {n_eff}")
    if n_eff>30 and ci == 0.95:
        # the most common case when the sample size is big enough
        # we use normal distribution
        # z = ppf(1-(1-0.95)/2) = 1.96
        # where ppf - the percent point function or
        # the inverse cumulative distribution function
        # of normal distribution
        z = 1.96
    else:
        # otherwise we calculate it from t distribution
        # 1-(1-ci)/2 comes from the fact that we are excluding values
        # outside confidence interval from both tails of distribution
        z=scipy.stats.t.ppf(1-(1-ci)/2, n_eff)
    #print(f"z: {z}")
    err = np.std(x)/np.sqrt(n_eff) * z
    #print(f"mean: {x_mean};  error: {err}")
    return x_mean, err

def sample_to_target_error(
        get_data_callback,
        target_error = None,
        target_eff_sample_size = None,
        timeout = 30,
        initial_sample_size = 100,
        tau = None,
        ci = 0.95):
    import time
    import numpy as np
    import logging
    logger = logging.getLogger("sample_to_target_error")
    #stop sampling criteria
    def end_loop(elapsed_time, current_error, eff_sample_size):
        if elapsed_time > timeout:
            logger.info('Reached timeout')
            return True
        #check if kwarg provided
        elif target_error is not None:
            if current_error <= target_error:
                logger.info("Reached target error")
                return True
        elif target_eff_sample_size is not None:
            if eff_sample_size >= target_eff_sample_size:
                logger.info("Reached effective sample size")
                return True
        else:
            return False
    #init timer
    start_time = time.time()
    n_samples = initial_sample_size
    #first sample
    x = get_data_callback(n_samples)
    #if non autocorr time provided
    if tau is None: tau = get_tau(x)
    #correlated data mean and err margin
    x_mean, x_err = correlated_data_mean_err(x, tau, ci)
    #sampling loop
    while True:
        #time passed
        logger.info(f'Criteria is not reached')
        logger.info('More data will be collected')
        #append new sample (correlated)
        new_sample = get_data_callback(n_samples)
        x=np.append(x, new_sample)
        #if non autocorr time provided
        if tau is None: tau = get_tau(new_sample)
        #next time take twice the amount of data points
        n_samples = n_samples*2
        #err, sample size, time passed
        x_mean, x_err = correlated_data_mean_err(x, tau, ci)
        n_samples_eff = n_samples/(2*tau)
        elapsed_time = time.time() - start_time
        logger.info(f"{x_err}, {n_samples_eff}, {elapsed_time}")
        #stop sampling?
        if end_loop(elapsed_time, x_err, n_samples_eff):
            break
    #Done
    logger.info(f'Mean: {x_mean}, err: {x_err}, eff_sample_size: {n_samples/(2*tau)}')
    return x_mean, x_err, n_samples/(2*tau)