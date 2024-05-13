import os
import logging
from copy import deepcopy 
logger = logging.getLogger(__name__)

import yaml

import file_operations

def _merge_configs(default_config, device_config) -> dict:
    """Recursively merges default and device-specific configurations."""
    merged = default_config.copy()
    for key, value in device_config.items():
        if (
            isinstance(value, dict)
            and key in default_config
            and isinstance(default_config[key], dict)
        ):
            merged[key] = _merge_configs(default_config[key], value)
        else:
            merged[key] = value
    return merged

def _load_device_config(config: str, hostname: str, defaults_values:str="default") -> dict:
    """Loads configuration for a specific device, falling back to defaults."""

    default_config = config.get("devices", {}).get(defaults_values, {})
    device_config = config.get("devices", {}).get(hostname, {})

    return _merge_configs(default_config, device_config)

def _load_device_commands(config: str, hostname: str, defaults_values:str="default") -> dict:
    """Loads configuration for a specific device, falling back to defaults."""

    device_config = config.get("commands", {}).get(hostname, {})

    return device_config

def _get_var(variable):
    variable = variable.strip()
    variable = variable.upper()
    if "ENV." in variable:
        var = variable.split("ENV.")[1]
        var = var.strip()
        var = var.upper()
        if os.environ.get(var):
            variable = os.environ.get(var)
        else:
            logger.warning(f"Environment variable {var} not found")
            variable = ""
    return variable

def load_inventory(filename: str) -> dict:
    """
    Load inventory of devices from  a file.
    use the inventory to load IP addresses and connection information for netmiko.
    :param filename: The file to load from.
    :return dict: The dictionary with the inventory loaded, and each hostname has either specific values or values from the default.
    """
    logger.debug("load_inventory")
    inventory = dict()
    inventory_content = file_operations.load_file_content(filename)
    if not inventory_content:
        logger.error(f"No inventory found in {filename}")
        return
    inventory_yaml = yaml.safe_load(inventory_content)
    logger.debug(
        f"Loaded {len(inventory_yaml.get('devices',{}).keys())} raw entries from inventory file {filename}"
    )

    for device_hostname in inventory_yaml.get("devices", {}).keys():
        if device_hostname == "default":
            continue
        device_dict = _load_device_config(inventory_yaml, device_hostname)
        inventory[device_hostname] = device_dict
    logger.debug(f"Depured {len(inventory.keys())} inventory entries from {filename}")
    return inventory

def load_commands(filename: str):
    logger.debug("load_commands")
    commands = dict()
    commands_content = file_operations.load_file_content(filename)
    if not commands_content:
        logger.error(f"No commands found in {filename}")
        return
    commands_yaml = yaml.safe_load(commands_content)
    logger.debug(
        f"Loaded commands for {len(commands_yaml.get('commands',{}).keys())} devices/roles from {filename}"
    )

    for commands_role_hostname in commands_yaml.get("commands", {}).keys():
        command_dict = _load_device_commands(commands_yaml, commands_role_hostname)
        commands[commands_role_hostname] = command_dict
    logger.debug(f"Loaded {len(commands.keys())} comands roles/devices entries from {filename}")
    logger.debug(f"Loaded {commands.keys()} comands ")
    logger.debug(f"{commands}")
    return commands

def generate_device_list(inventory: dict, commands: dict) -> list:
    """
    Receives the inventory and commands YAML as dictionaries
    Generate device dict per entry in the inventory
    translates the values corresponding to the netmiko library
    """
    logging.debug("create_device_list")
    for device, device_dict in inventory.items():
        translated_device_dict = dict()
        translated_device_dict["hostname"] = device
        translated_device_dict["ip"] = device_dict.get("connection", {}).get("default", {}).get("mgmt_ip", "")
        translated_device_dict["username"] = _get_var(device_dict.get("credentials", {}).get("username", ""))
        translated_device_dict["password"] = _get_var(device_dict.get("credentials", {}).get("password", ""))
        translated_device_dict["port"] = device_dict.get("connection", {}).get("default", {}).get("mgmt_port", 22)
        translated_device_dict["device_type"] = device_dict.get("vendor")
        # breakpoint()
        device_roles = [x.strip() for x in device_dict.get("roles", "").split(",")]
        device_roles = ["all"] if device_roles == [""] else device_roles
        if "all" not in device_roles:
            device_roles.append("all")
        logger.debug(f"Device {device} has roles {device_roles}")
        login_commands = deepcopy(device_dict.get("commands", []))
        translated_device_dict["commands"] = login_commands
        for role in device_roles:
            logger.debug(f"Device {device} searching commands for role {role}")
            if role in commands.keys():
                translated_device_dict["commands"].extend(commands.get(role,[]))
        else:
            translated_device_dict["commands"].extend(commands.get(device,[]))
        translated_device_dict["commands"] = list(dict.fromkeys(translated_device_dict["commands"]))

        logger.debug(f"Device {device} was translated as {translated_device_dict}")
        yield translated_device_dict







