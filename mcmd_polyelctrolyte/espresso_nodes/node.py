from logging import Logger
from executors import EspressoExecutorSalt, EspressoExecutorGel
from socket_nodes import Node

#an entry point to run the node in subprocesses
if __name__=="__main__":
    import argparse
    import sys
    parser = argparse.ArgumentParser(description='IP')
    parser.add_argument('IP',
                        metavar='IP',
                        type=str,
                        help='IP')
    parser.add_argument('PORT',
                        metavar='PORT',
                        type=int,
                        help='PORT')
    parser.add_argument('-l', 
                        metavar='l',
                        type = float,
                        help = 'box_size',
                        required=True)
    parser.add_argument('--salt', 
                        help = 'salt reservoir',
                        action='store_true',
                        required=False)
    parser.add_argument('--gel', 
                        help = 'add gel to the system',
                        action='store_true',
                        required=False)
    parser.add_argument('-MPC', 
                        metavar='MPC',
                        type = int,
                        help = 'particles between nodes',
                        required='--gel' in sys.argv)
    parser.add_argument('-bond_length', 
                        metavar='bond_length',
                        type = float,
                        help = 'bond length',
                        required='--gel' in sys.argv)
    parser.add_argument('-alpha', 
                        metavar='alpha',
                        type = float,
                        help = 'charged monomer ratio',
                        required='--gel' in sys.argv)
    parser.add_argument('-no_interaction', 
                        metavar='no_interaction',
                        help = 'switch off bonded and non bonded interaction',
                        type = bool,
                        required=False,
                        default = 1.0)              
    args = parser.parse_args()
    
    if '--salt' in sys.argv:
        import logging
        logging.basicConfig(level=logging.DEBUG, stream=open('salt.log', 'w'))
        from init_reservoir_system import init_reservoir_system
        logging.info('Initializing salt reservoir')
        if not args.no_interaction:
            from shared import NON_BONDED_ATTR
        else:
            logging.info('No interactions between particles')
            NON_BONDED_ATTR = None
        system = init_reservoir_system(args.l, NON_BONDED_ATTR)
        node = Node(args.IP, args.PORT, EspressoExecutorSalt, system)
        node.run()
    elif '--gel' in sys.argv:
        import logging
        logging.basicConfig(level=logging.DEBUG, stream=open('gel.log', 'w'))
        from init_diamond_system import init_diamond_system
        from shared import PARTICLE_ATTR
        logging.info('Initializing reservoir with a gel')
        if not args.no_interaction:
            from shared import NON_BONDED_ATTR, BONDED_ATTR
        else:
            logging.info('No interactions between particles')
            NON_BONDED_ATTR = None
            BONDED_ATTR = None
        system = init_diamond_system(
            args.MPC, args.bond_length, args.alpha, args.l,
            BONDED_ATTR, NON_BONDED_ATTR, PARTICLE_ATTR
            )
        node = Node(args.IP, args.PORT, EspressoExecutorGel, system)
        node.run()
