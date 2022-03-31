"""
This script is used to run espresso on the client side of a socket (Node)
The script should be run with subprocess.Popen method,
or one can use socket_nodes.utils.create_server_and_nodes method.

The code goes through the next steps:

- create parser with salt, gel specific arguments
- parse arguments
- initialize system <- espresso.System (see: init_reservoir_system.py, init_diamond_system.py)
- initialize node <- socket_nodes.Node(args.IP, args.PORT, ExecutorClass, system) where
    ExecutorClass is EspressoExecutorSalt for salt or EspressoExecutorGel for gel
    system passed as *arg to ExecutorClass.init()
- run an infinite loop node.run()
    the method loops through:
        0)Connects to the server
        1)Listen for incoming data
        2)Process request
        3)Send the results back

@author: Laktionov Mikhail
"""

from executors import EspressoExecutorSalt, EspressoExecutorGel
from socket_nodes import ExecutorNode as Node
import logging, os
PID = os.getpid()
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
    parser.add_argument('-alpha',
                        metavar='alpha',
                        type = float,
                        help = 'charged monomer ratio',
                        required='--gel' in sys.argv)
    #parser.add_argument('--no_interaction',
    #                    action='store_true',
    #                    help = 'switch off bonded and non bonded interaction',
    #                    required= False,
    #                    )
    parser.add_argument('-log_name',
                        metavar='log_name',
                        help = 'name of log file',
                        type = str,
                        required=False)

    args = parser.parse_args()
    logger = logging.getLogger("run_node.py")
    
    #logging
    import logging
    if '-log_name' in sys.argv:
        logging.basicConfig(level=logging.INFO, stream=open(args.log_name, 'w'))
        logger.debug("run_node.py DEBUG")
    logger.info("run_node.py started with args:")
    logger.info(' '.join(f'{k}={v}' for k, v in vars(args).items()))
    #set or disable interaction
    #if '--no_interaction' in sys.argv:
    #    logger.warning('No interactions between particles')
    #    NON_BONDED_ATTR = None
    #    BONDED_ATTR = None
    #else:
    #    from shared import NON_BONDED_ATTR, BONDED_ATTR
    #    logger.debug("loading non_bonded_interaction params from shared.py")
    from shared import NON_BONDED_ATTR, BONDED_ATTR
    #NON_BONDED_ATTR = None
    #BONDED_ATTR = None

    logger.info(f'non_bonded interaction params: {NON_BONDED_ATTR}')
    #init salt or gel
    if '--salt' in sys.argv:
        from init_reservoir_system import init_reservoir_system
        logger.info('Initializing salt reservoir')
        system = init_reservoir_system(box_l = args.l, non_bonded_attr = NON_BONDED_ATTR)
        node = Node(args.IP, args.PORT, EspressoExecutorSalt, system)
    elif '--gel' in sys.argv:
        from init_diamond_system import init_diamond_system
        logger.info('Initializing reservoir with a gel')
        from shared import PARTICLE_ATTR
        system = init_diamond_system(
            MPC = args.MPC, alpha = args.alpha, target_l = args.l,
            bonded_attr = BONDED_ATTR, non_bonded_attr = NON_BONDED_ATTR, particle_attr =PARTICLE_ATTR
            )
        node = Node(args.IP, args.PORT, EspressoExecutorGel, system)
    
    logger.info("Starting the node...")
    try:
        node.run()
    except Exception as e:
        logger.exception(e)
    logger.warning("Node is closed")
    
