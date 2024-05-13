import pyparsing as pp

digits = pp.Word(pp.nums)
ipv4_address = pp.Word(pp.nums + r"." )

mask_prefix = pp.Combine(pp.Word("/") + pp.Word(pp.nums))
mask_quads = pp.Word(pp.nums) + pp.Literal(".") + pp.Word(pp.nums) + pp.Literal(".") + pp.Word(pp.nums) + pp.Literal(".") + pp.Word(pp.nums)
mask_quads = pp.Combine(mask_quads)
mask_quads = pp.Word("/") + mask_quads
mask = mask_prefix | mask_quads

subnet = ipv4_address + mask

none_word = pp.Keyword("None")
one_or_more_spaces = pp.Suppress(pp.ZeroOrMore(pp.Literal(" ")))
new_line = pp.Suppress(pp.Regex(r"\r?\n"))
ignore_line = pp.Regex(r".*\r?\n")


# Router route-table definitions
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

interface_name = pp.Regex(r"[\w\d\-\/ ]{1,60}")
tunneled_bgp = pp.Literal("tunneled:BGP")
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

# Define the router route-table grammar
route_table_entry = (
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

igp_grammar = pp.OneOrMore(
        pp.Group(route_table_entry) |
        pp.Suppress(ignore_line)
    )


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
# router bgp routes vpn-ipv4 definitions
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
label = digits

# Define the BGP VPN-IPv4 Route grammar
bgp_vpn_ipv4_entry = (
    pp.AtLineStart(status_code("status_code")) 
    + prefix("prefix") 
    + local_pref("local_pref") 
    + med 
    + next_hop("next_hop") 
    + path_id("path_id") 
    + igp_cost("igp_cost") 
    + path("path") 
    + label("label")
    + pp.Suppress(pp.LineEnd())
)


bgp_grammar = pp.OneOrMore(
        pp.Group(bgp_vpn_ipv4_entry) | 
        pp.Suppress(ignore_line)
    )


service_name = pp.Word(pp.alphanums)
router_or_service = pp.Literal("Router:") | pp.Literal("Service:")
service_name_line = pp.Group(
        pp.Suppress(pp.Literal("Route Table"))
        + pp.Suppress(pp.Literal("(")) 
        + pp.Suppress(router_or_service)
        + service_name("service_name") 
        + pp.Suppress(pp.Literal(")"))
    )

service_grammar = pp.OneOrMore(
    service_name_line
    | pp.Suppress(ignore_line)
)


def parse_output(raw_output):
   results = igp_grammar.parse_string(raw_output)
   return results

def parse_service(raw_output):
   results = service_grammar.parse_string(raw_output)
   return results