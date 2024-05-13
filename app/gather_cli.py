import argparse
import ipaddress as ipa
import os
import re

import logging
logging.basicConfig(
    level=logging.INFO,  # Set the desired logging level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()

import orchestrator as orchestrator

def main():
    parser = argparse.ArgumentParser(description="Network gathering information")
    parser.add_argument("inventory", help="Yaml file where the inventory of devices is stored", default="inventory.yaml", type=str)
    parser.add_argument("commandset", help="Yaml file where the commands to execute are stored", default="commands.yaml", type=str)
    parser.add_argument("--output", choices=["per-device", "per-command", "single-file"], default="per-device" )
    parser.add_argument("--dry-run", help="Execute a dry run, but do not execute any commands", action="store_true", default=False )

    logging_group = parser.add_mutually_exclusive_group()  
    logging_group.add_argument("-d", "--debug", action="store_true", help="Enable debug logging")
    logging_group.add_argument("-q", "--quiet", action="store_true", help="Suppress output except critical errors")

    args = parser.parse_args()

    # Configure logging based on arguments
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    elif args.quiet: 
        logging.basicConfig(level=logging.ERROR)
        logger.setLevel(logging.ERROR)
    else:
        logging.basicConfig(level=logging.INFO)
        logger.setLevel(logging.INFO)
    
    orchestrator.remote_command_execution(args.inventory, args.commandset, args.dry_run,)



if __name__ == '__main__':
    main()

