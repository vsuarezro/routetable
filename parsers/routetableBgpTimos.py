

""" 
Route Table parser for SROS BGP table
show router <id>? bgp routes [vpn-ipv4]
"""

import socket
import re

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
        self.protocol = ""

        self.preference = ""        
        self.autonomus_system = ""
        self.route_distinguisher = ""
        self.flags = ""
        self.aspath = ""
        self.med = ""
        self.label = ""
        self.pathid = ""
        
    def __str__(self):
        str = "{prefix} {nexthop} {protocol}".format( 
            prefix = self.prefix, 
            nexthop = self.nexthop, 
            protocol = self.protocol )
        return str
        

class RouteTableBGPTimosParser:
    def __init__(self):
        # self.parse_string = parse_string
        self.route_table = dict()
        self.current_routerid = ""
        self.current_family = ""
        self.current_pack = None
        self.state = RouteTableBGPTimosParser.RoutingInformationStartState()
        
    def _loop(self, remaining_string):
        remain = self.state.process(remaining_string, self)
        return remain
            
    def process(self, remaining_string):
        logging.info("Parser start")
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
            route_list.append((pack.prefix,))
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
        match = re.search( r"show\s+router\s+(?P<routerid>\d*)\s*bgp\s*routes\s*(?P<family>vpn-ipv4)?\s*$", 
                           content, 
                           re.MULTILINE )
        if match:
            return "hvrp"
        return None

        
    class RoutingInformationStartState(object):
        def process(self, remaining_string, parser):
            match = re.search( r"show\s+router\s+(?P<routerid>\d*)\s*bgp\s*routes\s*(?P<family>vpn-ipv4)?\s*$", 
                               remaining_string, 
                               re.MULTILINE )
            if match:
                if match.group('routerid'):
                    router_id = match.group('routerid')
                else:
                    router_id = "Base"
                parser.current_routerid = router_id
                if match.group('family'):
                    family = match.group('family')
                else:
                    family = "ipv4"
                parser.current_family = family
                
                if router_id in parser.route_table:
                    logging.info("Found router <{router_id}> information at least a second time".format( router_id = router_id ) ) 
                if router_id not in parser.route_table:
                    parser.route_table[router_id] = []
                parser.state = RouteTableBGPTimosParser.CheckConsistencyState()
                logging.info("RoutingInformation router <{router_id}>".format( router_id = router_id ) ) 
                logging.info("RoutingInformation found at {start}".format(start=match.start()) )
                
                logging.debug("Routing information state <{}>".format(router_id) )
                return remaining_string[ match.end(): ]
            else:
                logging.info("No routing information found. Exiting") 
            
    class CheckConsistencyState(object):
        def process(self, remaining_string, parser):
            parser.state = RouteTableBGPTimosParser.TableStartState()
            return remaining_string
        
    class TableStartState(object):
        def process(self, remaining_string, parser):
            if "minor" in remaining_string[0:20].lower():
                # route table is empty, invalid router id
                parser.state = RouteTableBGPTimosParser.RoutingInformationStartState()
                logging.info("Invalid router Id <{router_id}>".format(router_id=parser.current_routerid) )
                return remaining_string
                
            match = re.search(r"-{2,}$", remaining_string, flags = re.MULTILINE)
            if match:
                logging.info("Router Id <{router_id}> route-table start".format(router_id=parser.current_routerid) )
                logging.debug("Start line <{}>".format(match.group()) )
                logging.debug("Remain string <{}>".format(remaining_string[ match.end(): match.end()+20 ]) )
                parser.state = RouteTableBGPTimosParser.PackCreateState()
                return remaining_string[ match.end(): ]

            logging.error("Malformed file. TableStart state <{}>".format(remaining_string[0:100].encode()) )
            parser.state = RouteTableBGPTimosParser.RoutingInformationStartState()
            return remaining_string            
        
    class PackCreateState(object):
        def process(self, remaining_string, parser):
            check_point = re.search(r"--", remaining_string[0:15])
            if check_point:
                logging.info("Router Id <{router_id}> has no routes".format(router_id=parser.current_routerid) )
                parser.state = RouteTableBGPTimosParser.RoutingInformationStartState()
                return remaining_string
            
            match = re.search(r"([\*ushdlx\>bpie\?]+)", remaining_string)
            if match:
                match_prefix = re.search(r"(\S+)", remaining_string[ match.end(): ])
                if match_prefix:
                    parser.current_pack = Pack( prefix = match_prefix.group(0) )
                    parser.current_pack.flags = match.group()
                    logging.debug("Pack create state <{}>".format(match_prefix.group(0)) )
                    logging.debug("Pack create state flags <{}>".format(match.group(0)) )
                    parser.state = RouteTableBGPTimosParser.LocalPreferenceState()
                    return remaining_string[ match.end() + match_prefix.end(): ]
            
            logging.error("Malformed file. Pack create {}".format(remaining_string[0:100]) )
            parser.state = RouteTableBGPTimosParser.RoutingInformationStartState()
            return remaining_string
                
    class LocalPreferenceState(object):
        def process(self, remaining_string, parser):
            match = re.search(r"\s(\d+)\s", remaining_string)
            if match:
                parser.current_pack.preference = match.group(0).strip()
                logging.debug("Local Preference <{}>".format(match.group(0).strip()) )
                parser.state = RouteTableBGPTimosParser.MEDState()
                return remaining_string[ match.end() : ]

            logging.error("Malformed file. Local Preference error {}".format(remaining_string[0:100]) )
            parser.state = RouteTableBGPTimosParser.RoutingInformationStartState()
            return remaining_string
        
    class MEDState(object):
        def process(self, remaining_string, parser):
            match = re.search(r"\s(\S+)\s*$", remaining_string, re.MULTILINE)
            if match:
                try:
                    med_value = int(match.group(0).strip())
                except ValueError:
                    if "none" in match.group(0).lower():
                        parser.current_pack.med = match.group(0).strip()                    
                        parser.state = RouteTableBGPTimosParser.NextHopState()
                        logging.debug("MED <{}>".format(match.group(0).strip()) )
                        return remaining_string[ match.end() : ]
                else:
                    parser.current_pack.med = match.group(0).strip()
                    parser.state = RouteTableBGPTimosParser.NextHopState()
                    logging.debug("MED <{}>".format(match.group(0).strip()) )
                    return remaining_string[ match.end() : ]
                
                # no valid value found
                logging.error("No valid MED <{}>".format(match.group(0).strip()) )
                parser.state = RouteTableBGPTimosParser.RoutingInformationStartState()
                return remaining_string

            logging.error("Malformed file. MED error <{}>".format(remaining_string[0:100].encode()) )
            parser.state = RouteTableBGPTimosParser.RoutingInformationStartState()
            return remaining_string

    class NextHopState(object):
        def process(self, remaining_string, parser):
            match_nexthop = re.search(r"(\S+)", remaining_string )
            if match_nexthop:
                if self._check_valid_ip(match_nexthop.group(0)):
                    parser.current_pack.nexthop = match_nexthop.group(0)
                    parser.state = RouteTableBGPTimosParser.PathIdState()
                    logging.debug("Nexthop {}".format(match_nexthop.group(0)) )
                    return remaining_string[ match_nexthop.end(): ]
                
                # no valid IP as next hop
                parser.state = RouteTableBGPTimosParser.RoutingInformationStartState()
                logging.error("No valid Next hop {}".format(remaining_string[0:100]) )
                return remaining_string

            logging.error("Malformed file. Next Hop error <{}>".format(remaining_string[0:100].encode()) )
            parser.state = RouteTableBGPTimosParser.RoutingInformationStartState()
            return remaining_string
            
        def _check_valid_ip(self, string):
            ip = string
            result = None
            try:
                socket.inet_aton(ip)
            except OSError:
                result = None
            else:
                result = "ipv4"

            if result:
                return result
                
            try:
                socket.inet_pton(socket.AF_INET6, ip)
            except OSError:
                result = None
            else:
                result = "ipv6"

            return result

    class PathIdState(object):
        def process(self, remaining_string, parser):
            match = re.search(r"(\S+)", remaining_string )
            if match:
                try:
                    int(match.group(0).strip())
                except ValueError:
                    if "none" in match.group(0).lower():
                        parser.current_pack.pathid = match.group(0).strip()                    
                        parser.state = RouteTableBGPTimosParser.LabelState()
                        logging.debug("PathId <{}>".format(match.group(0).strip()) )
                        return remaining_string[ match.end() : ]
                else:
                    parser.current_pack.pathid = match.group(0).strip()
                    parser.state = RouteTableBGPTimosParser.LabelState()
                    logging.debug("PathId <{}>".format(match.group(0).strip()) )
                    return remaining_string[ match.end() : ]
                
                # no valid value found
                logging.error("No valid Path id <{}>".format(match.group(0).strip()) )
                logging.debug("Path id error    <{}>".format(remaining_string[0:100].encode()) )
                parser.state = RouteTableBGPTimosParser.RoutingInformationStartState()
                return remaining_string
        
            logging.error("Malformed file. Path id error <{}>".format(remaining_string[0:100].encode()) )
            parser.state = RouteTableBGPTimosParser.RoutingInformationStartState()
            return remaining_string

    class LabelState(object):
        def process(self, remaining_string, parser):
            match = re.search(r"(\S+)$", remaining_string, re.MULTILINE )
            if match:
                try:
                    int(match.group(0).strip())
                except ValueError:
                    if "none" in match.group(0).lower():
                        parser.current_pack.label = match.group(0).strip()                    
                        parser.state = RouteTableBGPTimosParser.AsPathState()
                        logging.warning("No Label for this prefix: <{}>".format(match.group(0).strip()) )
                        logging.debug("Label <{}>".format(match.group(0).strip()) )
                        return remaining_string[ match.end() : ]
                else:
                    parser.current_pack.label = match.group(0).strip()
                    parser.state = RouteTableBGPTimosParser.AsPathState()
                    logging.debug("Label <{}>".format(match.group(0).strip()) )
                    return remaining_string[ match.end() : ]
                
                # no valid value found
                logging.error("No valid Label <{}>".format(match.group(0).strip()) )
                parser.state = RouteTableBGPTimosParser.RoutingInformationStartState()
                return remaining_string
        
            logging.error("Malformed file. Label error <{}>".format(remaining_string[0:100].encode()) )
            parser.state = RouteTableBGPTimosParser.RoutingInformationStartState()
            return remaining_string            
             
    class AsPathState(object):
        def process(self, remaining_string, parser):
            if "no as-path" in remaining_string[0:20].lower():
                parser.current_pack.aspath = "No As-Path"
                parser.state = RouteTableBGPTimosParser.AddPack()
                logging.debug("As Path <No As-Path>")
                match = re.search(r"\n", remaining_string[1:], re.MULTILINE )
                return remaining_string[ match.end() : ]
                
            match = re.search(r"([\d\s]+)$", remaining_string, re.MULTILINE )
            if match:                
                path = match.group(0).strip().split(' ')
                for id in path:
                    if id == '' or id == "\n":
                        continue
                    try:
                        int(id)
                    except ValueError:
                        logging.error("No valid AS id <{}>".format(id) )
                        logging.error("No valid AS Path <{}>".format(match.group(0).strip()) )
                        parser.current_pack.aspath = match.group(0).strip()
                        parser.state = RouteTableBGPTimosParser.RoutingInformationStartState()
                        return remaining_string
                
                parser.state = RouteTableBGPTimosParser.AddPack()
                parser.current_pack.aspath = match.group(0).strip()
                logging.debug("As Path <{}>".format(match.group(0).strip()) )
                return remaining_string[ match.end() : ]
            
            logging.error("Malformed file. AS error <{}>".format(remaining_string[0:100].encode()) )
            parser.state = RouteTableBGPTimosParser.RoutingInformationStartState()
            return remaining_string                
             
    class AddPack(object):
        def process(self, remaining_string, parser):
            parser.current_pack.protocol = "bgp {}".format(parser.current_family)
            parser.route_table[parser.current_routerid].append(parser.current_pack)
            logging.debug("Pack created {pack} on router {router_id}".format(
                    pack = parser.current_pack,
                    router_id = parser.current_routerid) )
            
            match = re.search(r"-{2,}", remaining_string[0:20] )
            if match:
                parser.state = RouteTableBGPTimosParser.RoutingInformationStartState()
                return remaining_string
            
            match = re.search(r"([\*ushdlx\>bpie\?]+)", remaining_string[0:20])
            if match:
                parser.state = RouteTableBGPTimosParser.PackCreateState()
                return remaining_string
            print ( "<", end="")
            print ( remaining_string[0:40].encode() , end="")
            print ( ">")
            #parser.state = RouteTableBGPTimosParser.RoutingInformationStartState()
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
    parser.add_argument("-o", "--outputfile", help="file to write the result's output " )
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
        r1 = RouteTableBGPTimosParser()
        r1.process(contents)

    with open(args.fileinput2) as file:
        contents = file.read()
        r2 = RouteTableBGPTimosParser()
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

    with open(sys.argv[1]) as file:
        contents = file.read()
        r1 = RouteTableBGPTimosParser()
        r1.process(contents)        
    for id in r1.routersID():
        for pr in r1.routes_nexthop_protocol(id):
            print(pr)