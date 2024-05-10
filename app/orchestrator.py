import logging

import storage
import file_operations


def list_timestamps(hostname: str = None):
    logging.info("list_timestamps")
    if hostname:
        return storage.get_list_of_timestamps(hostname)
    return storage.get_list_of_timestamps()

def fetch_single_device(ip_address: str):
    import network_interface

    pass

def fetch_devices_from_file(filename: str):
    pass

def load_routes_from_file(filename: str, timestamp: str):
    """
    Load routes from a file.
    :param filename: The file to load from.
    :param timestamp: The timestamp to save to the database.
    :return: None
    """
    logging.debug("load_routes_from_file")
    content = file_operations.load_file(filename)
    routes = parser(content, timestamp)
    storage.save_routes(routes)


def compare_routes(hostname: str, service: str, timestamp1: str, timestamp2: str):
    """
    Compare routes between two timestamps.
    :param hostname: The hostname of the device.
    :param service: The service name.
    :param timestamp1: The first timestamp.
    :param timestamp2: The second timestamp.
    :return: A dictionary containing the added, deleted, and changed routes.
    """
    logging.info("compare_routes")
    return storage.compare_routes(hostname, service, timestamp1, timestamp2)




def compare_routes(hostname, service, timestamp1, timestamp2):
    pass
