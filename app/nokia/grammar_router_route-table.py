
# -*- coding: utf-8 -*-

"""
Execute the parser for Nokia route_table_grammar when faced with an output similar to the following:
# show router route-table 

===============================================================================
Route Table (Router: Base)
===============================================================================
Dest Prefix[Flags]                            Type    Proto     Age        Pref
      Next Hop[Interface Name]                                    Metric   
-------------------------------------------------------------------------------
1.1.1.1/32 [B]                                Remote  BGP_LABEL 10h49m31s  170
       10.20.30.40 (tunneled:SR-ISIS:530001)                        100

the parser will return a pyparsing.ParseResults object with the following attributes:
"route": "1.1.1.1/32",
"flags": "B",
"route_type": "Remote",
"route_protocol": "BGP_LABEL",
"age": "10h49m31s",
"preference": "170",
"next_hop": "10.20.30.40",
"interface_next_hop": "tunneled:SR-ISIS:530001",
"metric": "100"

Comands on Nokia that are relevant for this grammar are:
show router [router_id] route-table

"""


import argparse 
import csv
import sys
import io

import pyparsing as pp
# pp.ParserElement.set_default_whitespace_chars("\t")
# Define the elements of the route table
# Dest Prefix[Flags]                            Type    Proto     Age        Pref
#       Next Hop[Interface Name]                                    Metric   
# -------------------------------------------------------------------------------
# 1.1.1.1/32 [B]                                Remote  BGP_LABEL 10h49m31s  170
#        10.20.30.40 (tunneled:SR-ISIS:530001)                        41
# 10.0.1.10/32 [L]                              Remote  ISIS      00h14m59s  18
#        10.20.30.41                                                  12
# 10.0.3.20/32 [L]                              Remote  BGP       25d20h48m  18
#        10.20.30.50                                                  8

ignore_line = pp.Regex(r".*\r?\n")
ipv4_address = pp.Word(pp.nums + r"." )

mask_prefix = pp.Combine(pp.Word("/") + pp.Word(pp.nums))
mask_quads = pp.Word(pp.nums) + pp.Literal(".") + pp.Word(pp.nums) + pp.Literal(".") + pp.Word(pp.nums) + pp.Literal(".") + pp.Word(pp.nums)
mask_quads = pp.Combine(mask_quads)
mask_quads = pp.Word("/") + mask_quads
mask = mask_prefix | mask_quads

subnet = ipv4_address + mask

digits = pp.Word(pp.nums)
none_word = pp.Keyword("None")
one_or_more_spaces = pp.Suppress(pp.ZeroOrMore(pp.Literal(" ")))
new_line = pp.Suppress(pp.Regex(r"\r?\n"))

asn = pp.Word(pp.nums)
community = digits
rd_asn = pp.Combine( asn + pp.Literal(":") + community )
rd_subnet = ipv4_address
rd_subnet_asn = pp.Combine( ipv4_address + pp.Literal(":") + community )

rd = pp.Combine( rd_asn | rd_subnet_asn )

as_path_label = pp.Combine( digits + pp.ZeroOrMore(pp.Literal(" ") + digits)  )
no_path = pp.Literal("No As-Path")

interface_name = pp.Regex(r"[\w\d\-\/ ]{1,60}")
tunneled_bgp = pp.Literal("tunneled:BGP")
# combinar con numer de tunel
tunneled_isis_sr = pp.Combine(pp.Literal("tunneled:SR-ISIS:") + digits)
tunneled_isis_sr_te = pp.Combine(pp.Literal("tunneled:SR-TE:") + digits)
tunneled_rsvp = pp.Combine(pp.Literal("tunneled:RSVP:") + digits)
age_hms = pp.Combine(digits + pp.Literal("h") + digits + pp.Literal("m") + digits + pp.Literal("s"))
age_dhm = pp.Combine(digits + pp.Literal("d") + digits + pp.Literal("h") + digits + pp.Literal("m"))
age_dh = pp.Combine(digits + pp.Literal("d") + digits + pp.Literal("h"))

route = pp.Combine( ipv4_address + mask )
flags = pp.Word("nBLS")
route_type = pp.Literal("Remote") | pp.Literal("Local") | pp.Literal("Blackh*")
route_protocol = pp.Literal("BGP_LABEL") | pp.Literal("ISIS") | pp.Literal("Static") | pp.Literal("BGP VPN") | pp.Literal("BGP") | pp.Literal("Aggr") | pp.Literal("Local")
age = age_hms | age_dhm | age_dh
preference = digits
interface_next_hop = tunneled_bgp | tunneled_isis_sr | tunneled_rsvp | tunneled_isis_sr_te
next_hop = ipv4_address | interface_name
metric = digits

@interface_name.set_parse_action
def clear_whitespaces(s: str, loc: int, tokens: pp.ParseResults):
    tokens[0] = tokens[0].strip()

# @ignore_line.set_parse_action
def ignore_line_action(s: str, loc: int, tokens: pp.ParseResults):
    print(tokens[0])

# Define the BGP VPN-IPv4 Route grammar
route_entry = (
    pp.AtLineStart(route("route")) 
    + pp.Opt( pp.Suppress(pp.Literal("[")) + flags("flags") + pp.Suppress(pp.Literal("]")) )
    + route_type("route_type") 
    + route_protocol("route_protocol") 
    + age("age") 
    + preference("preference")
    + pp.Opt(next_hop("next_hop"))
    + pp.Opt(pp.Suppress(pp.Literal("(")) + interface_next_hop("interface_next_hop") + pp.Suppress(pp.Literal(")")))
    + metric("metric")
    + pp.Suppress(pp.LineEnd())
)

route_table_grammar = pp.OneOrMore(
        pp.Group(route_entry) |
        pp.Suppress(ignore_line)
    )

def run_example():
    # Parse the BGP VPN-IPv4 Route
    result = route_entry.parse_string(
        """10.0.1.37/32 [L]                              Remote  ISIS      00h08m44s  18
       10.190.144.128                                               19
    """
    )

    # Print the parsed results
    print(result)

    result = route_table_grammar.parse_string(
    """1.1.1.1/32 [B]                                Remote  BGP_LABEL 10h43m16s  170
       10.190.3.146 (tunneled:SR-ISIS:310032)                       441
10.0.1.2/32 [L]                               Remote  ISIS      00h08m44s  18
       10.190.144.128                                               192
10.0.3.3/32 [L]                               Remote  ISIS      25d20h48m  18
       10.190.144.128                                               83
10.32.68.4/32 [B]                             Remote  BGP VPN   01d00h03m  170
       10.190.126.2 (tunneled:BGP)                                  1004
10.32.219.5/24                                Remote  BGP VPN   09h21m20s  170
       10.190.3.235 (tunneled:SR-ISIS:373749)                       25
10.33.15.6/32 [B]                             Remote  BGP VPN   09h21m14s  170
       10.190.118.2 (tunneled:SR-ISIS:404083)                       26
10.38.145.7/30                                Local   Local     0241d11h   0
       INTERFACE-NAME_1                                             0
10.38.147.8/29                                Local   Local     0241d11h   0
       INTERFACE-NAME_2                                             0
10.38.147.9/29                                Remote  BGP VPN   87d10h57m  170
       10.190.0.57 (tunneled:SR-ISIS:540152)                        37
10.38.147.10/32                               Remote  Static    0241d11h   5
       10.38.147.2                                                  100
10.38.147.11/32                               Remote  Static    0241d11h   5
       10.38.147.2                                                  100
10.38.147.12/30                               Remote  BGP VPN   87d10h57m  170
       10.190.0.57 (tunneled:SR-ISIS:5400001)                        400
10.170.38.13/31                               Local   Local     0146d07h   0
       To REMOTE-HOSTNAME                                           0
10.147.0.14/16                                Blackh* Static    0365d12h   5
       Black Hole                                                   1
    """
    )

    for item in result:
        print(item)
        print(item.get("route"), item.get("next_hop"), item.get("interface_next_hop"))

def run_parsing(data:str) -> pp.ParseResults:
    results = route_table_grammar.parse_string(data)
    return results

def filter_fields(fields, data):
    return dict((field, data.get(field)) for field in fields)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='show router bgp vpnv4 routes parsing')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--file', help='The file to parse.')
    group.add_argument('--example', help='Run the example with using embedded config', action='store_true')
    parser.add_argument('--fields', help='Use specified fields to save in a csv file', action='append')
    parser.add_argument('--output_file', help='Write result of parsing using specified file name', action='store')
    parser.add_argument('--version', action='version', version='%(prog)s 0.1')

    args = parser.parse_args()

    if args.fields is None:
        args.fields = ['route', 'next_hop', 'interface_next_hop', 'metric']

    if args.file:
        with open(args.file, 'r') as open_file:
            config = open_file.read()
        results = run_parsing(config)
        
        header = args.fields
        stream = io.StringIO()

        output = csv.DictWriter(stream, header, extrasaction='ignore')
        output.writeheader()
        for data in results:
            data = filter_fields(args.fields, data)
            output.writerow(data)
        stream.seek(0)
        if args.output_file:
            output_file = open(args.output_file, 'w')
        else:
            output_file = sys.stdout
        print(stream.read(), file=output_file)
        print(f"Total of {len(results)} routes")

    elif args.example:
        results = run_example()