# Finite Volume Monte-Carlo Molecular Dynamic Hybrid

## Motivation
Here we implement MCMD Hybrid model to model and study polyelectrolyte gel in a finite volume reservoir at different pressures and volumes. We are interested mostly in the desalination properties of aforesaid gels.
It has to be noted that a similar models have been implemented by the authors earlier. Though in those studies the reservoir the gel were immersed in has infinite volume. One can thought of this project as incremental study to the previous ones.

## Technical Notes

### Espressomd limitations
Espressomd provides excellent python interface to the fast C++/Cython written core. Unfortunately, we have failed to spawn two or more instances of espressomd.System in one python script, so it was decided to start separate processes of python interpreter each having one instance of espressomd.System. 
The nature of MC requires extensive communication between the instances, hence some kind of inter process communication (IPC) has to be implemented. There are several possible ways to do it e.g using pipes and sockets. The latter approach has been chosen since socket-based ICP better covered and documented in official and unofficial sources. Moreover, sockets allow to run instances of code on separate machines, thus it is more scalable.

### TCP/IP Socket
There is native library to create and use sockets in python. Usually one creates one server to serve multiple clients. In our case it was decided that the server side does the request to clients (nodes), where nodes employ python interface to molecular dynamics software.
TCP/IP sockets are two ways data channels that allows to exchange bytes over the network, the network can include local machine only i.e. 'localhost' or '127.0.0.1'. The one side of the channel is called server side, on the server side the socket is initialized with IP and PORT, after that several clients can bind to this socket creating their instances of client side socket.

### MCMD Network scheme

┌───────────────────┐                  two instances
│Server side        │             ┌────────────────────────┐
├───────────────────┤             │Node (Client) side      ├─┐
│ Monte-Carlo       │   Request   ├────────────────────────┤ │
│   -swap particles ├────────────►│ Molecular Dynamics     │ │
│   -change volume  │             │ (espressomd)           │ │
│                   │   Response  │   -integration         │ │
│ Major statistic   │◄────────────┤   -potential, kinetic  │ │
│                   │             │   energies             │ │
│ Manage results    │             │   -particle attributes │ │
└───────────────┬───┘             │                        │ │
   ▲            │                 │ Minors statistics      │ │
   │            ▼                 │   -sampling            │ │
 input       output               │   -mean, error         │ │
                                  └┬───────────────────────┘ │
                                   └─────────────────────────┘

For our purpose we have to use two instances of espressomd.System to integrate molecular dynamics equations, calculate potential and kinetic energies, manipulate particles. So two python interpreters are started and the processes try to create and connect client socket to the server socket with provided address. The scripts thereby should accept IP and PORT as arguments.

On server side Monte-Carlo routines are run, server sends request to add/remove particle, calculate energies, change system volume and etc. to the connected nodes to the data to proceed with Metropolis-Huntington algorithm.

For the purpose of hybrid model molecular dynamics integration steps precedes Monte-Carlo steps or vice versa. Some of the calculations tasks are moved to the nodes (molecular dynamics and some statistic) and can be effectively run asynchronous, whilst Monte-Carlo can only be executed synchronous so the corresponding routines are running on the server side. The other reason to move some statistic to the nodes is to decrease an amount of data going through the socket. 

### Request-responce loop

                 ┌───────┐
        ┌────────┤Request├──────────┐
        │        │string │          │
        │        └───────┘          ▼
     Server                        Node
        ▲      ┌─────────────┐      │
        │      │  Responce   │      │
        └──────┤  picklable  ├──────┘
               │python object│
               └─────────────┘
The interaction between the server and the nodes are simple request-response loop. 

Let us illustrate it on the next example. Suppose we want to exchange particles between two espresso systems and reverse this move if the MC algorithm tells us. 

Server side:
    Asynchronous:
    1a. Send request to remove particle to node 0 and return its attributes
    1b. Send request to add particle to node 1 and return its id
    2a. Send request to calculate potential energy to node 0
    2b. Send request to calculate potential energy to node 1
    Synchronous:
    3. Wait for the requests results (4 requests)
    4. Calculate accepting criterion for Metropolis Huntington
    If rejected:
    Asynchronous:
    5a. Send request to add particle to node 0 with the same attributes it had been removed
    5b. Send request to remove particle with id from the request (1b) to node 1
    Synchronous:
    6. Wait for the requests results (2 requests)

Let us assume the move has been accepted by the Metropolis Huntington, then the nodes would receive the next requests and answer with corresponding responses.

Node 0:
    1. Got request to remove a particle
    2. Select random particle, store its attributes, remove it
    3. Send the attributes as pickled dictionary to the server
    4. Got request to calculate potential energy
    5. Send the value of potential energy as pickled float to the server

Node 1:
    1. Got request to add a particle
    2. Add particle with random coordinates
    3. Send added particle id as pickled integer to the server
    4. Got request to calculate potential energy
    5. Send the value of potential energy as pickled float to the server

On the server side we have synchronous and asynchronous part of the code,
synchronous means that the code could not be executed if the previous code had not done. Asynchronous means that the next operation does not have to wait for the result of the previous one. 

Take a look the line 2a and 2b on the server side. Having request to calculate potential energy to node 0 been sent we do not have to wait for the result, so we send request 2b immediately after 2a. Potential energy calculation in the both nodes are run in parallel. In order to decide whether we will accept this step, we have to know potential energy in both instances of espressomd.System, so we wait for the result, see the line 3 in server side.

To denote that the order of request is irrelevant and the result are not needed right now, asynchronous operation written with letter indexing.

## Equilibration and sampling

## Notes on statistics

## Manage result data

    
     