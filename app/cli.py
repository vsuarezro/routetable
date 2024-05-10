import argparse
import ipaddress as ipa
import logging
import os
import re

import app.orchestrator as orchestrator
import formatter

logging.basicConfig(
    level=logging.INFO,  # Set the desired logging level
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()

def validate_timestamp(timestamp):
    timestamp_regex = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{2}:[0-9]{2}$") # e.g. 2024-05-09_08:30
    if not timestamp_regex.match(timestamp):
        return False
    return True

def main():
    parser = argparse.ArgumentParser(description="Network configuration comparison tool")
    # Mutually exclusive group for 'fetch' and 'load'
    commands_group = parser.add_mutually_exclusive_group(required=True)  
    commands_group.add_argument("--fetch", help="Fetch routes from a device (IP address) or a file of devices", type=str)  # Note: nargs and const for enhanced handling
    commands_group.add_argument("--load", nargs=2, metavar=("FILENAME", "TIMESTAMP"), help="Load routes from a file with a timestamp")
    commands_group.add_argument("--list", nargs='?', metavar="HOSTNAME", const='all', help="List available timestamps (optionally filter by hostname)", type=str) 
    commands_group.add_argument("--compare", nargs=4, metavar=("HOSTNAME", "SERVICE", "TIMESTAMP1", "TIMESTAMP2" ), help="Compare routes between timestamps")

    logging_group = parser.add_mutually_exclusive_group()  
    logging_group.add_argument("-d", "--debug", action="store_true", help="Enable debug logging")
    logging_group.add_argument("-q", "--quiet", action="store_true", help="Suppress output except critical errors")

    compare_group = parser.add_argument_group("compare_options")

    compare_group.add_argument(
        "--output", 
        choices=["text", "csv", "yaml", "json", "xml", "table"],
        default="text",
        help="Select output format (for compare command)"
    )

    args = parser.parse_args()
    print(args)
    
    # Configure logging based on arguments
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    elif args.quiet: 
        logging.basicConfig(level=logging.CRITICAL)

    if args.list == 'all':
        timestamp_list = orchestrator.list_timestamps()
        if timestamp_list is None or len(timestamp_list) == 0:
            logging.warning("No timestamps found")
            return
        for timestamp in timestamp_list:
            print(timestamp.join(","))
        return
    elif args.list:
        timestamp_list = orchestrator.list_timestamps(args.list)
        if timestamp_list is None or len(timestamp_list) == 0:
            logging.warning(f"No timestamps found for {args.list}")
            return
        for timestamp in timestamp_list:
            print(timestamp.join(","))
        return
    
    if args.fetch:
        # Check if the IP address is valid and if it is call fetch_single_device
        # if it's not an ip address then check if the filename exists, if it exists call fetch_devices_from_file
        try:
            ip_address = ipa.ip_address(args.fetch)
        except ValueError:
            ip_address = None
        if ip_address:
            orchestrator.fetch_single_device(args.fetch)
        elif os.path.isfile(args.fetch):
            orchestrator.fetch_devices_from_file(args.fetch)
        else:
            logging.error(f"{args.fetch} is not a valid IP address or file")
            return
    if args.load:
        filename, timestamp = args.load
        if not validate_timestamp(timestamp):
            logging.error(f"{timestamp} is not a valid timestamp. format is YYYY-MM-DD_HH:MM")
            return
        if not os.path.isfile(filename):
            logging.error(f"{filename} does not exist")
            return
        orchestrator.load_routes_from_file(filename, timestamp)
        logging.info(f"Loaded routes from {filename} at {timestamp}")
        return
    if args.compare:
        hostname, service, timestamp1, timestamp2 = args.compare
        if not validate_timestamp(timestamp1):
            logging.error(f"{timestamp} is not a valid timestamp. format is YYYY-MM-DD_HH:MM")
            return
        if not validate_timestamp(timestamp2):
            logging.error(f"{timestamp} is not a valid timestamp. format is YYYY-MM-DD_HH:MM")
            return
        if timestamp1 == timestamp2:
            logging.error(f"{timestamp1} and {timestamp2} are the same")
            return
        if timestamp1 > timestamp2:
            timestamp1, timestamp2 = timestamp2, timestamp1
            logging.warning(f"Swapped timestamps {timestamp1} and {timestamp2}")

        routes_comparison = orchestrator.compare_routes(hostname, service, timestamp1, timestamp2)
        if routes_comparison is None:
            logging.error("No routes found")
            return
        output_formatter = formatter.fommatter_function.get(args.output)
        print(output_formatter(routes_comparison))
        return


if __name__ == '__main__':
    main()

