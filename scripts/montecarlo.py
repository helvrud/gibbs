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
        m = self.move()
        if m == None: return self.current_state
        else: reversal, accept_criterion = m
        if self.accept(accept_criterion):
            self.update_state(reversal)
            self.on_accept()
        else:
            self.reverse(reversal)
            self.on_reject()
        return self.current_state
