


"""
Execute the parser for Nokia route_table_grammar when faced with an output similar to the following:
# show router bgp routes vpn-ipv4
===============================================================================
 BGP Router ID:192.0.2.146      AS:65500       Local AS:65500      
===============================================================================
 Legend -
 Status codes  : u - used, s - suppressed, h - history, d - decayed, * - valid
                 l - leaked, x - stale, > - best, b - backup, p - purge
 Origin codes  : i - IGP, e - EGP, ? - incomplete

===============================================================================
BGP VPN-IPv4 Routes
===============================================================================
Flag  Network                                            LocalPref   MED
      Nexthop (Router)                                   Path-Id     IGP Cost
      As-Path                                                        Label
-------------------------------------------------------------------------------
u*>?  65500:10:1.2.3.4/32                                90          None
      10.20.30.40                                        409912231   100
      16960                                                          16000

the parser will return a pyparsing.ParseResults object with the following attributes:
"status_code": "u*>?",
"prefix": "65500:10:1.2.3.4/32",
"local_pref": "90",
"med": "None",
"next_hop": "10.20.30.40",
"path_id": "409912231",
"igp_cost": "100",
"path": "16960",
"label": "16000"

Comands on Nokia that are relevant for this grammar are:
show router [router_id] route-table

"""
import argparse 
import csv
import sys
import io

import pyparsing as pp
pp.ParserElement.set_default_whitespace_chars("\t")
# Define the elements of the BGP VPN-IPv4 Route

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

status_code = pp.Word("ushd*lx>bpie?")
prefix = pp.Combine(rd + pp.Literal(":") + pp.Combine( ipv4_address + mask ))
local_pref = digits
med = digits | none_word
next_hop = ipv4_address
path_id = digits
igp_cost = digits
path = as_path_label | no_path
label = digits + new_line



# Define the BGP VPN-IPv4 Route grammar
bgp_vpn_ipv4_route = (
    pp.AtLineStart(status_code("status_code")) 
    + one_or_more_spaces 
    + prefix("prefix") 
    + one_or_more_spaces 
    + local_pref("local_pref") 
    + one_or_more_spaces 
    + med 
    + new_line
    + one_or_more_spaces 
    + next_hop("next_hop") 
    + one_or_more_spaces 
    + path_id("path_id") 
    + one_or_more_spaces 
    + igp_cost("igp_cost") 
    + new_line
    + one_or_more_spaces 
    + path("path") 
    + one_or_more_spaces 
    + label("label")
)

bgp_vpn_ipv4_grammar = pp.OneOrMore(
        pp.Group(bgp_vpn_ipv4_route) | 
        pp.Suppress(ignore_line)
    )

def run_example():
    # Parse the BGP VPN-IPv4 Route
    result = bgp_vpn_ipv4_route.parse_string(
        """*>?   12345:17:192.168.0.1/32                         100         None
        10.20.30.1                                         123789456   15
        12345 12345                                                    300000
    """
    )

    # Print the parsed results
    print(result)

    result = bgp_vpn_ipv4_grammar.parse_string(
    """*>?   12345:1700:10.168.196.1/32                         100         None
        10.100.1.0                                         100112211   15
        12345 12345                                                    520001
*?    12345:1700:10.168.196.2/32                         100         None
    10.100.1.1                                         100112222   15
    12345 12345                                                    511222
*?    12345:1700:10.168.196.3/32                         100         None
    10.200.1.2                                         100112233   15
    No As-Path                                                     511333
*?    10.200.90.253:4321:200.100.260.44/30               100         None
      10.200.90.253                                      100112244   100
      64000 64000 4321                                               62444
    """
    )

    for item in result:
        print(item)
        print(item.get("prefix"))


def run_parsing(data:str) -> pp.ParseResults:
    results = bgp_vpn_ipv4_grammar.parse_string(data)
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
        args.fields = ['status_code', 'prefix', 'next_hop']

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
            
    elif args.example:
        results = run_example()