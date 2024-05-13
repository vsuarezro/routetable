import argparse
import ipaddress as ipa
import os
import re

import logging

logging.basicConfig(
    level=logging.INFO,  # Set the desired logging level
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger()

import orchestrator as orchestrator
import formatter


def validate_timestamp(timestamp):
    timestamp_regex = re.compile(
        r"^[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{2}:[0-9]{2}$"
    )  # e.g. 2024-05-09_08:30
    if not timestamp_regex.match(timestamp):
        return False
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Networks tools. Compare and Screape"
    )
    # main options, valid for more than one command
    parser.add_argument("-i","--inventory-file", type=str, default="inventory.yaml", help="YAML file with device information")
    parser.add_argument("-c", "--commands-file", type=str, default="command.yaml", help="YAML file with commands to execute")
    parser.add_argument("-f","--device-filter", type=str, default="all", help="Filter devices (hostname or role)")

    # Main commands: compare and scrape
    subparsers = parser.add_subparsers(title="Commands", dest="command")

    # Scrape command
    parser_scrape = subparsers.add_parser("scrape", help="Scrape device configurations")

    # Scrape mutually exclusive options
    scrape_output_group = parser_scrape.add_mutually_exclusive_group()  # Mutually exclusive group within 'scrape'
    scrape_output_group.add_argument("--scrape-output", choices=["per-device", "per-command", "single-file"], default="per-device", help="Select the number of files to create where to save the outputs, per-device saves a single file per device, per-command saves a file per combination of hostname+command and single-file saves a single file with all the outputs. Default is per-device")
    scrape_output_group.add_argument("--dry-run", action="store_true", default=False, help="Simulate scrape without connecting")

    # Compare Command
    parser_compare = subparsers.add_parser("compare", help="Compare configurations")
    parser_compare.add_argument("--table", choices=["route","bgp",], default="route", help="Select route-table or bgp-table to compare. Defaults to route"
                                )
    parser_compare.add_argument("--compare-output", choices=["text", "csv", "yaml", "json", "xml", "table"], default="text", help="Select output format (for compare command)",
                                )
    compare_group = parser_compare.add_mutually_exclusive_group()  # Mutually exclusive group within 'compare'
    compare_group.add_argument(
        "--query",
        nargs=4,
        metavar=("HOSTNAME","SERVICE","TIMESTAMP1", "TIMESTAMP2"),
        help="Compare routes between two timestamps",
    )
    compare_group.add_argument(
        "--load-file",
        nargs=4,
        metavar=("FILENAME", "HOSTNAME", "TIMESTAMP", "VENDOR"),
        help="Load routes from a file with a timestamp",
    )
    compare_group.add_argument(
        "--fetch",
        action="store_true",
        help="Fetch routes from a device (IP address) or a file of devices",
    )
    compare_group.add_argument(
        "--list",
        nargs="?",
        metavar="HOSTNAME",
        const="all",
        help="List available timestamps (optionally filter by hostname)",
        type=str,
    )
    compare_group.add_argument(
        "--remove",
        nargs=2,
        metavar=("HOSTNAME","TIMESTAMP"),
        help="Remove specific compare checkpoints from the database",
    )


    # Logging options
    logging_group = parser.add_mutually_exclusive_group()
    logging_group.add_argument(
        "-d", "--debug", action="store_true", help="Enable debug logging"
    )
    logging_group.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress output except critical errors",
    )
    
    args = parser.parse_args()
    print(args)

    # Configure logging based on arguments
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    elif args.quiet:
        logging.basicConfig(level=logging.ERROR)
        logger.setLevel(logging.ERROR)
    else:
        logging.basicConfig(level=logging.INFO, 
                            format="%(name)s - %(levelname)s - %(message)s",
                            )
        logger.setLevel(logging.INFO)

    if args.command == "scrape":
        logger.info("Starting CLI scrape command")
        output_list = orchestrator.remote_command_execution(args.inventory_file, args.commands_file, args.device_filter, args.dry_run,)
        if args.dry_run:
            exit()
        if output_list is None or len(output_list) == 0 or output_list is [None]:
            logger.error("No output received")
            exit()
        devices_executed = [x.get('hostname') for x in output_list]
        logger.info(f"Commands executed on {len(devices_executed)} devices")
        logger.info(f"Commands executed on devices: {' '.join(devices_executed)} devices")

        output_formatter = formatter.scrape_formatter_function.get(args.scrape_output)
        tuples_list = output_formatter(output_list)
        for filename, output in tuples_list:
            with open(filename, "w") as f:
                f.write(output)
                print(f"File {filename}\nOUTPUT: {output}")


    if args.command == "compare":
        logger.info("Starting compare command")
        logger.info(f"Reference table:{args.table}")
        if not args.list and not args.query and not args.load_file and not args.fetch and not args.remove:
            args.list = "all"

        if args.list:
            logger.info("Listing available timestamps")
            timestamp_list = orchestrator.list_timestamps(None if args.list == "all" else args.list)
            if timestamp_list is None or len(timestamp_list) == 0:
                logger.warning("No timestamps found")
                return
            for timestamp in timestamp_list:
                print(" ".join([str(x) for x in timestamp]))
            exit()
    
        if args.load_file:
            logger.info("Loading routes from file")

            filename, hostname, timestamp, vendor = args.load_file
            if not validate_timestamp(timestamp):
                logger.error(
                    f"{timestamp} is not a valid timestamp. format is YYYY-MM-DD_HH:MM"
                )
                return
            orchestrator.load_routes_from_file(filename, hostname, timestamp, vendor)
            logger.info(f"Loaded routes from {filename} at {timestamp}")
            exit()

        if args.query:
            logger.info("Comparing routes between two timestamps")
            hostname, service, timestamp1, timestamp2 = args.query
            if not validate_timestamp(timestamp1):
                logger.error(
                    f"{timestamp} is not a valid timestamp. format is YYYY-MM-DD_HH:MM"
                )
                return
            if not validate_timestamp(timestamp2):
                logger.error(
                    f"{timestamp} is not a valid timestamp. format is YYYY-MM-DD_HH:MM"
                )
                return
            if timestamp1 == timestamp2:
                logger.error(f"{timestamp1} and {timestamp2} are the same")
                return
            if timestamp1 > timestamp2:
                timestamp1, timestamp2 = timestamp2, timestamp1
                logger.warning(f"Swapped timestamps {timestamp1} and {timestamp2}")

            routes_comparison = orchestrator.compare_routes(
                hostname, service, timestamp1, timestamp2
            )
            if routes_comparison is None:
                logger.error("No routes found")
                return
            output_formatter = formatter.fommatter_function.get(args.compare_output)
            print(
                output_formatter(
                    routes_comparison, hostname, service, timestamp1, timestamp2
                )
            )
            exit()

        if args.remove:
            logger.info("Removing routes")
            hostname, timestamp = args.remove
            if not validate_timestamp(timestamp):
                logger.error(
                    f"{timestamp} is not a valid timestamp. format is YYYY-MM-DD_HH:MM"
                )
                exit()
            entries_deleted = orchestrator.remove_routes_for_device(
                hostname, timestamp
            )
            logger.info(f"Entries deleted: {entries_deleted}")
            exit()


    exit()

 
    # Compare options
    compare_group = parser.add_argument_group("compare_options")
    compare_group.add_argument(
        "--table",
        choices=[
            "route-table",
            "bgp-table",
        ],
        default="route-table",
        help="Select route-table or bgp-table to compare. Defaults to route-table",
    )
    compare_group.add_argument(
        "--times",
        nargs=4,
        metavar=("HOSTNAME","SERVICE","TIMESTAMP1", "TIMESTAMP2"),
        help="Compare routes between two timestamps",
    )
    compare_group.add_argument(
        "--load-file",
        nargs=4,
        metavar=("FILENAME", "HOSTNAME", "TIMESTAMP", "VENDOR"),
        help="Load routes from a file with a timestamp",
    )
    compare_group.add_argument(
        "--fetch",
        action="store_true",
        help="Fetch routes from a device (IP address) or a file of devices",
    )
    compare_group.add_argument(
        "--list",
        nargs="?",
        metavar="HOSTNAME",
        const="all",
        help="List available timestamps (optionally filter by hostname)",
        type=str,
    )
    compare_group.add_argument(
        "--remove",
        nargs=2,
        metavar=("HOSTNAME","TIMESTAMP"),
        help="Remove specific compare checkpoints from the database",
    )
    compare_group.add_argument(
        "--compare-output",
        choices=["text", "csv", "yaml", "json", "xml", "table"],
        default="text",
        help="Select output format (for compare command)",
    )

    args = parser.parse_args()
    print(args)
    exit()
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

    # List command
    if args.list == "all":
        timestamp_list = orchestrator.list_timestamps()
        if timestamp_list is None or len(timestamp_list) == 0:
            logger.warning("No timestamps found")
            return
        for timestamp in timestamp_list:
            print(" ".join(timestamp))
        return
    elif args.list:
        timestamp_list = orchestrator.list_timestamps(args.list)
        if timestamp_list is None or len(timestamp_list) == 0:
            logger.warning(f"No timestamps found for {args.list}")
            return
        for timestamp in timestamp_list:
            print(" ".join(timestamp))
        return

    # Fetch command
    if args.fetch:
        if args.inventory:
            logger.info(f"Getting inventory from {args.inventory}")
            if os.path.isfile(args.inventory):
                logger.debug(
                    f"Loading inventory from {os.path.abspath(args.inventory)}"
                )
                orchestrator.load_inventory(args.inventory)

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

    # Load command
    if args.load:
        filename, hostname, timestamp, vendor = args.load
        if not validate_timestamp(timestamp):
            logger.error(
                f"{timestamp} is not a valid timestamp. format is YYYY-MM-DD_HH:MM"
            )
            return
        if not os.path.isfile(filename):
            logger.error(f"{filename} does not exist")
            return
        orchestrator.load_routes_from_file(filename, hostname, timestamp, vendor)
        logger.info(f"Loaded routes from {filename} at {timestamp}")
        return

    # Comapre command
    if args.compare:
        hostname, service, timestamp1, timestamp2 = args.compare
        if not validate_timestamp(timestamp1):
            logger.error(
                f"{timestamp} is not a valid timestamp. format is YYYY-MM-DD_HH:MM"
            )
            return
        if not validate_timestamp(timestamp2):
            logger.error(
                f"{timestamp} is not a valid timestamp. format is YYYY-MM-DD_HH:MM"
            )
            return
        if timestamp1 == timestamp2:
            logger.error(f"{timestamp1} and {timestamp2} are the same")
            return
        if timestamp1 > timestamp2:
            timestamp1, timestamp2 = timestamp2, timestamp1
            logger.warning(f"Swapped timestamps {timestamp1} and {timestamp2}")

        routes_comparison = orchestrator.compare_routes(
            hostname, service, timestamp1, timestamp2
        )
        if routes_comparison is None:
            logger.error("No routes found")
            return
        output_formatter = formatter.fommatter_function.get(args.compare_output)
        print(
            output_formatter(
                routes_comparison, hostname, service, timestamp1, timestamp2
            )
        )
        return


if __name__ == "__main__":
    main()
