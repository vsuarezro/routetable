""" 
Route Table parser for Huawei Versatile Router Platform 
disply ip routing table
"""

import re
import socket

import os
import logging
logging.basicConfig(# filename=os.path.basename(__file__) + ".log", 
                    filemode="w",
                    format='%(asctime)-15s %(levelname)-5s :%(name)s: %(message)s',
                    level=logging.INFO)

class Pack(object):
    def __init__(self, prefix):
        self.prefix = prefix
        self.nexthop = ""
        self.nexthop_interface = ""
        self.protocol = ""
        self.preference = ""
        self.flag = ""
        
    def __str__(self):
        str = "{prefix} {nexthop} {protocol}".format( 
            prefix = self.prefix, 
            nexthop = self.nexthop, 
            protocol = self.protocol )
        return str
        

class RouteTableHVRPParser:
    def __init__(self):
        # self.parse_string = parse_string
        self.route_table = dict()
        self.current_routerid = ""
        self.current_pack = None
        self.state = RouteTableHVRPParser.RoutingInformationStartState()
        
    def _loop(self, remaining_string):
        remain = self.state.process(remaining_string, self)
        return remain
            
    def process(self, remaining_string):
        logging.info("Parser start")
        # remain = self._loop( remaining_string )
        remain = remaining_string
        while remain:
            remain = self._loop( remain )
        logging.info("Content Processed")
        return self.route_table
        
    def routes(self, router_id):
        if router_id not in self.route_table:
            logging.info("Router <{router_id}> not in data".format(router_id = router_id))
            return
        
        route_list = []
        for pack in self.route_table[router_id]:
            route_list.append( (pack.prefix, ) )
        return route_list

    def routes_nexthop(self, router_id):
        if router_id not in self.route_table:
            logging.info("Router <{router_id}> not in data".format(router_id = router_id))
            return

        route_list = []
        for pack in self.route_table[router_id]:
            route_list.append( (pack.prefix, pack.nexthop) )
        return route_list

    def routes_protocol(self, router_id):
        if router_id not in self.route_table:
            logging.info("Router <{router_id}> not in data".format(router_id = router_id))
            return

        route_list = []
        for pack in self.route_table[router_id]:
            route_list.append( (pack.protocol, pack.prefix) )
        return route_list
        
    def routes_nexthop_protocol(self, router_id):
        if router_id not in self.route_table:
            logging.info("Router <{router_id}> not in data".format(router_id = router_id))
            return

        route_list = []
        for pack in self.route_table[router_id]:
            route_list.append( (pack.protocol, pack.prefix, pack.nexthop) )
        return route_list
    
    def routersID(self):
        return self.route_table.keys()

    def inspect(self, content):
        match = re.search( r"di(?:[splay])? ip ro(?:[uting-table])?\s*(?P<inst>vpn-instance)?\s*(?P<vpnname>[\w]*)\s*$", content, re.MULTILINE )
        if match:
            return "hvrp"
        return None
        
    class RoutingInformationStartState(object):
        def process(self, remaining_string, parser):
            # route_table_pattern = re.compile(r"show router (\d*)\s?route-table\s+")
            match = re.search( r"di(?:[splay])?\s+ip\s+ro(?:[uting-table])?\s*(?P<inst>vpn-instance)?\s*(?P<vpnname>[\w]*)\s*$", remaining_string, re.MULTILINE )
            if match:
                if match.group('vpnname'):
                    router_id = match.group('vpnname')
                else:
                    router_id = "Base"
                parser.current_routerid = router_id
                if router_id in parser.route_table:
                    logging.info("Found router <{router_id}> information at least a second time".format( router_id = router_id ) ) 
                if router_id not in parser.route_table:
                    parser.route_table[router_id] = []
                parser.state = RouteTableHVRPParser.TableStartState()
                logging.info("RoutingInformation router <{router_id}>".format( router_id = router_id ) ) 
                logging.info("RoutingInformation found at {start}".format(start=match.start()) )
                
                logging.debug("Routing information state <{}>".format(router_id) )
                return remaining_string[ match.end(): ]
            else:
                logging.info("No routing information found. Exiting") 
            
    class TableStartState(object):
        def process(self, remaining_string, parser):
            # check for errors first
            
            # check if duplicated line of display ip routing-table output
            # match = re.search( r"di(?:[splay])* ip ro(?:[uting\-table])*\s*(?P<inst>vpn-instance)?\s*(?P<vpnname>[\w]*)\s*$", remaining_string, re.MULTILINE )
            # if match: 
                # logging.debug("Duplicated line for display information. Router <{}>".format(parser.current_routerid) )
                # parser.state = RouteTableHVRPParser.TableStartState()
                # return remaining_string[ match.end(): ]

            # check if table is really starting 
            check_point = re.search(r"(?:Routing Tables:)\s+(?P<vpnname>[\w]+)", remaining_string)
            if check_point:
                if "public" in check_point.group('vpnname').lower() and parser.current_routerid == "Base":
                    logging.debug("Route table <{}> check pass".format(parser.current_routerid) )
                elif check_point.group('vpnname') == parser.current_routerid:
                    logging.debug("Route table <{}> check pass".format(parser.current_routerid) )
                elif check_point.group('vpnname') != parser.current_routerid:
                    logging.info("Router Id <{router_id}> route-table not found".format(router_id=parser.current_routerid) )
                    logging.info("Router Id <{router_id}> found instead".format(router_id=check_point.group('vpnname')) )
                    parser.state = RouteTableHVRPParser.RoutingInformationStartState()
                    return remaining_string
            else:
                logging.error("Malformed file. TableStartState not found" )
                logging.error("Context string {}".format(remaining_string[0:100]) )
                parser.state = RouteTableHVRPParser.RoutingInformationStartState()
                return remaining_string
            
            # look for start of table
            match = re.search(r"[Ii]nterface\s*$", remaining_string, re.MULTILINE)
            if match:
                logging.debug("TableStartState found")
                parser.state = RouteTableHVRPParser.PackCreateState()
                return remaining_string[ match.end(): ]
                
            logging.error("Malformed file. TableStartState not found" )
            logging.error("Context string {}".format(remaining_string[0:100]) )
            parser.state = RouteTableHVRPParser.RoutingInformationStartState()
            return remaining_string
                        
        
    class PackCreateState(object):
        def process(self, remaining_string, parser):
            # check for errors
            
            
            # grab first string, it has to be a ip prefix, otherwise is a continuation
            match_prefix = re.search(r"(\S+)", remaining_string)
            if match_prefix:
                checkip = self._check_prefix( match_prefix.group(0) )
                if  checkip == None: # not an IP address
                    logging.debug("Possible continuation of previous Pack <{}> {}".format(
                        parser.current_pack.prefix, match_prefix.group(0)) )
                    parser.current_pack = Pack( prefix = parser.current_pack.prefix )
                    parser.state = RouteTableHVRPParser.ProtocolState()
                    return remaining_string
                elif checkip == "ipv4" or checkip == "ipv6": 
                    logging.debug("Pack create state <{}>".format(match_prefix.group(0).strip()) )
                    parser.current_pack = Pack( prefix = match_prefix.group(0) )
                    parser.state = RouteTableHVRPParser.ProtocolState()
                    return remaining_string[ match_prefix.end(): ]
                else:
                    logging.error("Something happened")
                    parser.state = RouteTableHVRPParser.RoutingInformationStartState()
                    return remaining_string
            
            logging.error("Malformed file. Pack create error")
            parser.state = RouteTableHVRPParser.RoutingInformationStartState()
            return remaining_string
        
        def _check_prefix(self, string):
            prefix = string
            ip = prefix.split("/", 1)
            if len(ip) != 2: # not splitted, then not a valid prefix
                return None
            try:
                socket.inet_aton(ip[0])
            except OSError:
                result = None
            else:
                if int(ip[1]) >=0 and int(ip[1]) <= 32:
                    result = "ipv4"
                else:
                    result = None

            if result:
                return result
                
            try:
                socket.inet_pton(socket.AF_INET6, ip[0])
            except OSError:
                result = None
            else:
                if int(ip[1]) >=0 and int(ip[1]) <= 128:
                    result = "ipv6"
                else:
                    result = None
                    
            if result:
                return result
            
            return None

    class ProtocolState:
        def process(self, remaining_string, parser):
            match = re.search(r"(\w+)\s", remaining_string )
            if match:
                if parser.current_pack.protocol != "":
                    logging.debug("Pack continuation <{}>".format(parser.current_pack.prefix) )
                parser.current_pack.protocol = match.group(0).strip()
                parser.state = RouteTableHVRPParser.PreferenceState()
                logging.debug("Protocol <{}>".format(parser.current_pack.protocol))
                return remaining_string[ match.end(): ]
            
            logging.error("Malformed file. Protocol Error")
            parser.state = RouteTableHVRPParser.RoutingInformationStartState()
            return remaining_string

    class PreferenceState:
        def process(self, remaining_string, parser):
            match = re.search(r"\s(\d)+\s", remaining_string , re.MULTILINE)
            if match:
                parser.current_pack.preference = match.group(0).strip()
                parser.state = RouteTableHVRPParser.MetricState()
                logging.debug("preference <{}>".format(parser.current_pack.preference))
                return remaining_string[ match.end(): ]
            
            logging.error("Malformed file. Preference error" )
            parser.state = RouteTableHVRPParser.RoutingInformationStartState()
            return remaining_string
            
    class MetricState(object):
        def process(self, remaining_string, parser):
            match = re.search(r"(\d)+\s", remaining_string)
            if match:
                parser.current_pack.metric = match.group(0).strip()
                parser.state = RouteTableHVRPParser.FlagState()
                # **************** 
                # parser.route_table[parser.current_routerid].append(parser.current_pack)
                
                # logging.debug("Pack created {pack} on router {router_id}".format(
                    # pack = parser.current_pack,
                    # router_id = parser.current_routerid) )
                return remaining_string[ match.end(): ]

            logging.error("Malformed file. Metric error")
            parser.state = RouteTableHVRPParser.RoutingInformationStartState()
            return remaining_string
            
    class FlagState(object):
        def process(self, remaining_string, parser):
            match = re.search(r"(\w)\s+", remaining_string )
            if match:
                parser.current_pack.flag = match.group(0).strip()
                parser.state = RouteTableHVRPParser.NextHopState()
                return remaining_string[ match.end(): ]

            logging.error("Malformed file. Flag error")
            parser.state = RouteTableHVRPParser.RoutingInformationStartState()
            return remaining_string
            
    class NextHopState(object):
        def process(self, remaining_string, parser):            
            match_nexthop = re.search(r"(\S)+", remaining_string )
            if match_nexthop:
                parser.current_pack.nexthop = match_nexthop.group(0)
                parser.state = RouteTableHVRPParser.InterfaceState()
                return remaining_string[ match_nexthop.end(): ]

            logging.error("Malformed file. Next Hop error")
            parser.state = RouteTableHVRPParser.RoutingInformationStartState()
            return remaining_string
            
    class InterfaceState(object):
        def process(self, remaining_string, parser):
            
            match = re.search(r"(\S+)\s*$", remaining_string, re.MULTILINE)
            if match:
                parser.current_pack.nexthop_interface = match.group().strip() 
                parser.route_table[parser.current_routerid].append(parser.current_pack)

                logging.debug("Pack created {pack} on router {router_id}".format(
                    pack = parser.current_pack,
                    router_id = parser.current_routerid) )

            check_end_table = re.search(r"\r?\n\r?\n", remaining_string[match.end()-1:match.end()+2], re.MULTILINE )
            # check if next entry is an empty string. End of route table
            if check_end_table:
                parser.state = RouteTableHVRPParser.RoutingInformationStartState()
            else:
                parser.state = RouteTableHVRPParser.PackCreateState()
                
            return remaining_string[ match.end(): ]
            
            logging.error("Malformed file. Interface error" )
            parser.state = RouteTableHVRPParser.RoutingInformationStartState()
            return remaining_string
                


class View(object):
    def __init__(self, new_stream):
        self._out_newstream = sys.stdout
        if new_stream != None:
            self._out_newstream = new_stream
    
    def redirect(self):
        self._old_stream = sys.stdout
        sys.stdout = self._out_newstream

    def reset(self):
        sys.stdout = self._old_stream
        
    def __enter__(self):
        self._old_stream = sys.stdout
        sys.stdout = self._out_newstream
    
    def __exit__(self):
        sys.stdout = self._old_stream

class TablePrint(object):
    def __init__(self, columns_number = 3, separator = " "):
        space = int(75 / columns_number)
        self._base_string = "{!s:<" + str(space) + "}"
        self._separator = separator
                
    def print(self, *args):
        for arg in args:
            if type(arg) is tuple:
                for item in arg:
                    print ( self._base_string.format( item ), end="" )
                    print ( self._separator , end="" )
            else:
                print ( self._base_string.format( arg ), end="" )
                print ( self._separator , end="" )
        print()
        

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("fileinput1", help="file with 'show router <id> route-table' information")
    parser.add_argument("fileinput2", help="file with 'show router <id> route-table' information")
    parser.add_argument("-o", "--outputfile", help="file to drop the result's output " )
    parser.add_argument("-v", "--verbose", help="set level of verbosity", choices=["info", "debug", "error", "none"], default="info")
    parser.add_argument("-nh","--nexthop", help="check also next hop", action="store_true")
    parser.add_argument("-p", "--protocol", help="check also protocol", action="store_true")
    args = parser.parse_args()
    
    if args.verbose == "debug":
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
    if args.verbose == "none":
        logger = logging.getLogger()
        logger.setLevel(51)
    if args.verbose == "error":
        logger = logging.getLogger()
        logger.setLevel(logging.ERROR)
    if args.verbose == "info":
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
    
    view = None
    if args.outputfile != None:
        stream = open(args.outputfile, "w", encoding="utf-8")
        view = View(stream)
        view.redirect()
    
    start = time.perf_counter()
    
    with open(args.fileinput1) as file:
        contents = file.read()
        r1 = RouteTableHVRPParser()
        r1.process(contents)

    with open(args.fileinput2) as file:
        contents = file.read()
        r2 = RouteTableHVRPParser()
        r2.process(contents)
    
    if args.protocol and args.nexthop:
        columns = 5
        header = ["RouterId","Estatus","Protocol", "Prefix", "NextHop"]
    elif args.protocol or args.nexthop:
        columns = 4
        if args.protocol:
            header = ["RouterId", "Estatus","Protocol", "Prefix"]
        if args.nexthop:
            header = ["RouterId", "Estatus", "Prefix", "NextHop"]
    else:
        columns = 3
        header = ["RouterId","Estatus", "Prefix"]
    if view != None: # view to a file
        t = TablePrint(columns, separator=",")
    else: # view to screen
        t = TablePrint(columns)
    t.print(*header)
        
    for routerid in r1.routersID():
        if args.nexthop and args.protocol:
            setr1 = set ( r1.routes_nexthop_protocol(routerid) )
        elif args.protocol and not args.nexthop:
            setr1 = set ( r1.routes_protocol(routerid) )
        elif not args.protocol and args.nexthop:
            setr1 = set ( r1.routes_nexthop(routerid) )
        else:
            setr1 = set ( r1.routes(routerid) )
            
        if routerid in r2.routersID():
            if args.nexthop and args.protocol:
                setr2 = set ( r2.routes_nexthop_protocol(routerid) )
            elif args.protocol and not args.nexthop:
                setr2 = set ( r2.routes_protocol(routerid) )
            elif not args.protocol and args.nexthop:
                setr2 = set ( r2.routes_nexthop(routerid) )
            else:
                setr2 = set ( r2.routes(routerid) )
                
            missing_routes = setr1 - setr2
            new_routes = setr2 - setr1
            
            for pack in missing_routes:
                t.print( routerid, "missing", pack )

            for pack in new_routes:
                t.print( routerid, "new_route", pack )

        else:
            logging.critical("Router id <{router_id}> not found on second file input".format(router_id=routerid) )
    if view:
        view.reset()
        
    end = time.perf_counter()
    print (end - start)
                    
if __name__ == '__main__':
    import sys
    import time
    import argparse

    main()