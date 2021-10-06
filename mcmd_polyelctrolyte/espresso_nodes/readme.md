# Espressomd node
This directory contains concrete implementation of socket_nodes.ExecutorNode class and concrete implementation of socket_nodes.ExecutorLocalScopeOnly class. 

An instance of socket_nodes.ExecutorNode connects an arbitrary executable code to a server via TCP/IP socket when IP and PORT are provided. The instance node = socket_nodes.ExecutorNode(IP, PORT, ...) provide a method node.run(). The method has an infinite loop in it that listens to the socket for input commands and tries to execute it with built-in python method eval().

An instance of socket_nodes.ExecutorNode accepts class inherited from socket_nodes.ExecutorNode that contains executable code. socket_nodes.ExecutorNode delegates request execution to the instance of socket_nodes.ExecutorLocalScopeOnly. An instance of of executor class contains an instance os espressomd.System and user defined function to work with espressomd.System e.g. to populate system, to sample variable or to manipulate system in any other way.

## Motivation
One can not create more than one instance of espressomd.System in one process python interpreter. Separate python interpreter processes has to be spawn and communicate with each other.

## Structure
   node.py
  ┌──────────────────────────────────────────────┐
  │Node(IP, PORT, ExecutorClass, *args, **kwargs)│
  ├──────────────────────────────────────────────┤
  │ run() {listen, recv, execute, send}          │
  │                                              │
┌─┤ executor = Executor(*args, **kwargs)         │
│ │                                              │
│ │ execute(request)                             │
│ └──────────────────────────────────────────────┘
│    executors.py
│   ┌────────────────────────────────────┐
└──►│Executor(system : espressomd.System)│
    ├────────────────────────────────────┤
    │ execute(request)                   │
    │   {eval(request, scope)}           │
    │                                    │
  ┌─┤ system added to local scope        │
  │ └────────────────────────────────────┘
  │    init_reservoir_system.py
  │    init_diamond_system.py
  │   ┌────────────────────────────┐
  └──►│instantiated and initialized│
      │     espressomd.System      │
      └────────────────────────────┘

shared.py - contains data, parameters and variables shared between all the other scripts in this folder. There are such parameters as attributes of all kinds of particles, interaction parameters.

init_diamond_system.py and init_reservoir_system.py contains routines needed to create an espressomd.System instance of a given volume for the box with a gel and one with a salt, respectively. The scripts can be run standalone to debug. In this scripts we initialize integrator parameters, set bonded and non bonded interaction for the existing and future added particles.

executors.py contains two classes inherited from socket_nodes.ExecutorLocalScopeOnly class, one for the node which simulates salt and the other for the gel. When method execute(request) is called, the request is tried to be executed with eval(request, scope), where the scope includes an instance of espressomd.System and function defined as a class members of ExecutorClass by user.

node.py script to be run with subprocess.Popen, shell or similar. It accepts IP, PORT of a server required args, the user also has to provide arguments to instantiate salt or gel system. With provided arguments the script will do the next steps: 
 - creates salt or gel espressomd.System system
 - creates Executor object executor and add system as a member
 - creates Node object node and add executor as a member
 - runs infinite loop node.run()