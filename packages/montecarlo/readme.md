# Monte-Carlo particle and volume exchange

This is Monte-Carlo part of hybrid MCMD method. In our study we have to exchange ion pair between a salt reservoir and a polyelectrolyte gel. Both are espressomd.System objects. Moreover to model external pressure we should also be able to change system volume in a correlated manner.

## Tech notes

Scripts employ in-house python package socket_nodes to forego one instance only limit of the espressomd. Socket_nodes provides a way to instantiate multiple instances of espressomd.System and to communicate to them via TCP/IP sockets. Check espresso_nodes/readme.md for more info.

## Abstract Monte-Carlo class

In libmontecarlo.py we define abstract class agnostic to concrete implementation of the object it acts on. The class is classic Metropolis-Hastings algorithm in python code.

## Concrete Monte-Carlo

Inheriting MonteCarloBase from libmontecarlo.py we make concrete implementation.

### Ion pair exchange

ion_pair.py script provide a way to equilibrate ion pairs between two espressomd.System systems, providing they have compatible properties (e.g. same particles attribute) and sample particle distribution between this two systems.
An essential part of this class is that it has an instance of socket_nodes.Server, the latter provides a way to communicate with espressomd.System systems.
