"""
Module to parse network unstructured output.
This is the interface to the grammar files.
"""

import nokia.grammar as nokia_parser


VENDOR_PARSERS = {
    "nokia": nokia_parser,
    # "cisco_xe": cisco_xe_parser,
    # "cisco_xr": cisco_xr_parser,
}

def select_parser(vendor_name):
    return VENDOR_PARSERS.get(vendor_name.lower())

def parse(vendor_name, raw_output, hostname, timestamp):
    parser = select_parser(vendor_name)
    if not parser:
        raise ValueError(f"Unsupported vendor: {vendor_name}") 

    routes = parser.parse_output(raw_output)
    service_list = parser.parse_service(raw_output)
    service = service_list[0].get('service_name') if service_list else None

    for route in routes:
        route['hostname'] = hostname
        route['service'] = service
        route['timestamp'] = timestamp

    return routes