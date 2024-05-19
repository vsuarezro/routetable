import os
import logging

logger = logging.getLogger(__name__)

import yaml

import storage
database_url = "routes.sqlite3"
storage.initialize_database(database_url)
import netparser
import file_operations
import yaml_operations
import network_interface

def list_timestamps(hostname: str = None):
    logger.info("list_timestamps")
    if hostname:
        return storage.get_list_of_timestamps(hostname, )
    return storage.get_list_of_timestamps()

def remove_routes_for_device(hostname: str, timestamp: str):
    logger.info("remove_route")
    rows_deleted = storage.remove_routes(hostname, timestamp, )
    return rows_deleted

def fetch_single_device(ip_address: str):
    import network_interface

    pass


def fetch_devices_from_file(filename: str):
    import network_interface

    pass


def load_routes_from_file(filename: str, hostname: str, timestamp: str, vendor: str):
    """
    Load routes from a file.
    :param filename: The file to load from.
    :param timestamp: The timestamp to save to the database.
    :return: None
    """
    logger.debug("load_routes_from_file")
    content = file_operations.load_file_content(filename)
    routes = netparser.parse(vendor, content, hostname, timestamp)
    logger.info(f"Loaded {len(routes)} routes from {filename}")
    storage.save_routes(timestamp, routes, )
    logger.info(f"Saved {len(routes)} routes to the database")


def compare_routes(hostname: str, service: str, timestamp1: str, timestamp2: str):
    """
    Compare routes between two timestamps.
    :param hostname: The hostname of the device.
    :param service: The service name.
    :param timestamp1: The first timestamp.
    :param timestamp2: The second timestamp.
    :return: A dictionary containing the added, deleted, and changed routes.
    """
    logger.info("compare_routes")
    return storage.compare_routes(
        hostname, service, timestamp1, timestamp2, 
    )


def remote_command_execution(inventory_filename: str, command_filename: str, device_filter: str="all", dry_run_flag: bool = False,):
    """
    Gather inventory of devices from a file.
    :param filename: The file to load from.
    :param device_filter: from the inventory file only run it on filtered devices.
    :param dry_run_flag: A flag to enable dry run mode.
    :return: None
    """
    logger.debug("remote_command_execution")
    if device_filter == "all":
        logger.warning("Device filter not yet implemented")
        logger.info("Running on all devices")
        device_filter = None
    inventory = yaml_operations.load_inventory(inventory_filename)
    if not inventory:
        logger.error("No inventory found")
        return
    commands = yaml_operations.load_commands(command_filename)
    if not commands:
        logger.error("No commands found")
        return
    
    device_list = [x for x in yaml_operations.generate_device_list(inventory, commands)]
    logger.info(f"Preparing to execute commands on {len(device_list)} devices")
    logger.info(f"Devices to execute commands on: {[x.get('hostname') for x in device_list]}")
    if dry_run_flag:
        from pprint import pprint
        logger.info("Dry run mode enabled")
        logger.info(f"Inventory created: ##########")
        pprint(inventory)
        logger.info(f"Commands created: ##########")
        pprint(commands)
        logger.info(f"device_list created: ##########")
        pprint(device_list)
        logger.info("Dry run mode finished")
        return

    output_list = network_interface.execute_devices_commands(device_list)

    return output_list
