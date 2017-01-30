import os
import sys
sys.path.insert(0, os.path.abspath('..'))

import unittest
from parsers import routetableBgpTimos


class TestParserTimos(unittest.TestCase):
    
    def test_routersID(self):
        text = """*A:7750# show router 99 bgp routes 
===============================================================================
 BGP Router ID:14.191.131.2     AS:65000       Local AS:65000      
===============================================================================
 Legend -
 Status codes  : u - used, s - suppressed, h - history, d - decayed, * - valid
                 l - leaked, x - stale, > - best, b - backup, p - purge
 Origin codes  : i - IGP, e - EGP, ? - incomplete

===============================================================================
BGP IPv4 Routes
===============================================================================
Flag  Network                                            LocalPref   MED
      Nexthop (Router)                                   Path-Id     Label
      As-Path                                                        
-------------------------------------------------------------------------------
u*>?  1.1.1.3/32                                         100         None
      14.191.131.3                                       1779        131045
      65002                                                           
u*>?  1.1.2.3/32                                         100         None
      14.191.131.3                                       1781        131045
      65002                                                           
u*>?  10.238.3.0/31                                      100         0
      14.191.131.3                                       1894        131019
      No As-Path                                                      
-------------------------------------------------------------------------------
       """
        parser = routetableBgpTimos.RouteTableBGPTimosParser()
        parser.process(text)
        self.assertEqual( ["99"] , list(parser.routersID()) )
    
    def test_routersID_base(self):
        text = """*A:7750#       show router  bgp  routes        
===============================================================================
 BGP Router ID:14.191.131.2     AS:65000       Local AS:65000      
===============================================================================
 Legend -
 Status codes  : u - used, s - suppressed, h - history, d - decayed, * - valid
                 l - leaked, x - stale, > - best, b - backup, p - purge
 Origin codes  : i - IGP, e - EGP, ? - incomplete

===============================================================================
BGP IPv4 Routes
===============================================================================
Flag  Network                                            LocalPref   MED
      Nexthop (Router)                                   Path-Id     Label
      As-Path                                                        
-------------------------------------------------------------------------------
u*>?  1.1.1.3/32                                         100         None
      14.191.131.3                                       1779        131045
      65002                                                           
u*>?  1.1.2.3/32                                         100         None
      14.191.131.3                                       1781        131045
      65002                                                           
u*>?  10.238.3.0/31                                      100         0
      14.191.131.3                                       1894        131019
      No As-Path                                                      
-------------------------------------------------------------------------------
       """

        parser = routetableBgpTimos.RouteTableBGPTimosParser()
        parser.process(text)
        self.assertEqual( ["Base"] , list(parser.routersID()) )

    def test_multiple_tables(self):
        text = """*A:7750# show router bgp routes 
===============================================================================
 BGP Router ID:14.191.131.2     AS:65000       Local AS:65000      
===============================================================================
 Legend -
 Status codes  : u - used, s - suppressed, h - history, d - decayed, * - valid
                 l - leaked, x - stale, > - best, b - backup, p - purge
 Origin codes  : i - IGP, e - EGP, ? - incomplete

===============================================================================
BGP IPv4 Routes
===============================================================================
Flag  Network                                            LocalPref   MED
      Nexthop (Router)                                   Path-Id     Label
      As-Path                                                        
-------------------------------------------------------------------------------
u*>?  1.1.1.3/32                                         100         None
      14.191.131.3                                       1779        131045
      65002                                                           
-------------------------------------------------------------------------------
*A:7750# show router 43214321 bgp routes 
===============================================================================
 BGP Router ID:14.191.131.2     AS:65000       Local AS:65000      
===============================================================================
 Legend -
 Status codes  : u - used, s - suppressed, h - history, d - decayed, * - valid
                 l - leaked, x - stale, > - best, b - backup, p - purge
 Origin codes  : i - IGP, e - EGP, ? - incomplete

===============================================================================
BGP IPv4 Routes
===============================================================================
Flag  Network                                            LocalPref   MED
      Nexthop (Router)                                   Path-Id     Label
      As-Path                                                        
-------------------------------------------------------------------------------
u*>?  1.1.1.3/32                                         100         None
      14.191.131.3                                       1779        131045
      65002                                                           
-------------------------------------------------------------------------------
*A:7750# show   router  12345 bgp     routes 
===============================================================================
 BGP Router ID:14.191.131.2     AS:65000       Local AS:65000      
===============================================================================
 Legend -
 Status codes  : u - used, s - suppressed, h - history, d - decayed, * - valid
                 l - leaked, x - stale, > - best, b - backup, p - purge
 Origin codes  : i - IGP, e - EGP, ? - incomplete

===============================================================================
BGP IPv4 Routes
===============================================================================
Flag  Network                                            LocalPref   MED
      Nexthop (Router)                                   Path-Id     Label
      As-Path                                                        
-------------------------------------------------------------------------------
u*>?  1.1.1.3/32                                         100         None
      14.191.131.3                                       1779        131045
      65002                                                           
-------------------------------------------------------------------------------
       """
        parser = routetableBgpTimos.RouteTableBGPTimosParser()
        parser.process(text)
        self.assertEqual( sorted(["12345", "43214321", "Base"]) , sorted(list(parser.routersID())) ) 
    
    def test_one_route(self):
        text = """*A:7750# show   router  12345 bgp     routes 
===============================================================================
 BGP Router ID:14.191.131.2     AS:65000       Local AS:65000      
===============================================================================
 Legend -
 Status codes  : u - used, s - suppressed, h - history, d - decayed, * - valid
                 l - leaked, x - stale, > - best, b - backup, p - purge
 Origin codes  : i - IGP, e - EGP, ? - incomplete

===============================================================================
BGP IPv4 Routes
===============================================================================
Flag  Network                                            LocalPref   MED
      Nexthop (Router)                                   Path-Id     Label
      As-Path                                                        
-------------------------------------------------------------------------------
u*>?  1.1.1.2/32                                         100         None
      14.191.131.3                                       1779        131045
      65002                                                           
-------------------------------------------------------------------------------
       """
        parser = routetableBgpTimos.RouteTableBGPTimosParser()
        parser.process(text)
        self.assertEqual( [("1.1.1.2/32",)] , 
                          parser.routes("12345") 
                        ) 
    
    def test_one_route_nexthop(self):
        text = """*A:7750# show   router  999 bgp     routes 
===============================================================================
 BGP Router ID:14.191.131.2     AS:65000       Local AS:65000      
===============================================================================
 Legend -
 Status codes  : u - used, s - suppressed, h - history, d - decayed, * - valid
                 l - leaked, x - stale, > - best, b - backup, p - purge
 Origin codes  : i - IGP, e - EGP, ? - incomplete

===============================================================================
BGP IPv4 Routes
===============================================================================
Flag  Network                                            LocalPref   MED
      Nexthop (Router)                                   Path-Id     Label
      As-Path                                                        
-------------------------------------------------------------------------------
u*>?  1.1.1.2/32                                         100         None
      14.191.131.3                                       1779        131045
      65002                                                           
-------------------------------------------------------------------------------
       """
        parser = routetableBgpTimos.RouteTableBGPTimosParser()
        parser.process(text)
        self.assertEqual( [("1.1.1.2/32","14.191.131.3",)] , 
                          parser.routes_nexthop("999") 
                        ) 
    
    def test_route_protocol(self):
        text = """*A:7750# show   router   bgp     routes 
===============================================================================
 BGP Router ID:14.191.131.2     AS:65000       Local AS:65000      
===============================================================================
 Legend -
 Status codes  : u - used, s - suppressed, h - history, d - decayed, * - valid
                 l - leaked, x - stale, > - best, b - backup, p - purge
 Origin codes  : i - IGP, e - EGP, ? - incomplete

===============================================================================
BGP IPv4 Routes
===============================================================================
Flag  Network                                            LocalPref   MED
      Nexthop (Router)                                   Path-Id     Label
      As-Path                                                        
-------------------------------------------------------------------------------
u*>i  1.1.2.3/32                                         100         None
      14.191.131.3                                       1779        131045
      65002                                                           
-------------------------------------------------------------------------------
       """
        parser = routetableBgpTimos.RouteTableBGPTimosParser()
        parser.process(text)
        self.assertEqual( [("bgp ipv4","1.1.2.3/32",)] , 
                          parser.routes_protocol("Base") 
                        ) 
    
    def test_route_nexthop_protocol(self):
        text = """*A:7750# show   router   bgp     routes 
===============================================================================
 BGP Router ID:14.191.131.2     AS:65000       Local AS:65000      
===============================================================================
 Legend -
 Status codes  : u - used, s - suppressed, h - history, d - decayed, * - valid
                 l - leaked, x - stale, > - best, b - backup, p - purge
 Origin codes  : i - IGP, e - EGP, ? - incomplete

===============================================================================
BGP IPv4 Routes
===============================================================================
Flag  Network                                            LocalPref   MED
      Nexthop (Router)                                   Path-Id     Label
      As-Path                                                        
-------------------------------------------------------------------------------
u*>i  1.1.2.3/32                                         100         None
      14.191.131.3                                       1779        131045
      65002                                                           
-------------------------------------------------------------------------------
       """
        parser = routetableBgpTimos.RouteTableBGPTimosParser()
        parser.process(text)
        self.assertEqual( [("bgp ipv4","1.1.2.3/32","14.191.131.3")] ,
                          parser.routes_nexthop_protocol("Base") 
                        ) 
    
    def test_multiple_routes(self):
        text = """*A:7750# show   router   12345        bgp     routes 
===============================================================================
 BGP Router ID:14.191.131.2     AS:65000       Local AS:65000      
===============================================================================
 Legend -
 Status codes  : u - used, s - suppressed, h - history, d - decayed, * - valid
                 l - leaked, x - stale, > - best, b - backup, p - purge
 Origin codes  : i - IGP, e - EGP, ? - incomplete

===============================================================================
BGP IPv4 Routes
===============================================================================
Flag  Network                                            LocalPref   MED
      Nexthop (Router)                                   Path-Id     Label
      As-Path                                                        
-------------------------------------------------------------------------------
u*>?  1.1.1.2/32                                         100         None
      14.191.131.3                                       1779        131045
      65002                                                           
u*>?  1.1.1.3/32                                         100         145
      14.191.131.3                                       1781        131045
      65002                                                           
u*>?  1.1.2.1/32                                         100         10
      14.191.131.3                                       1894        131
      No As-Path                                                      
u*>?  89.75.232.0/24                                     100         632
      14.191.131.3                                       4           119
      No As-Path                                                      
-------------------------------------------------------------------------------
       """
        parser = routetableBgpTimos.RouteTableBGPTimosParser()
        parser.process(text)
        self.assertEqual( sorted( [("1.1.1.2/32",), ("1.1.1.3/32",), ("1.1.2.1/32",), ("89.75.232.0/24",)] ) , 
                          sorted ( parser.routes("12345") )
                        ) 
    
    def test_multiple_routes_nexthop_protocol(self):
        text = """*A:7750# show   router   923823        bgp     routes 
===============================================================================
 BGP Router ID:14.191.131.2     AS:65000       Local AS:65000      
===============================================================================
 Legend -
 Status codes  : u - used, s - suppressed, h - history, d - decayed, * - valid
                 l - leaked, x - stale, > - best, b - backup, p - purge
 Origin codes  : i - IGP, e - EGP, ? - incomplete

===============================================================================
BGP IPv4 Routes
===============================================================================
Flag  Network                                            LocalPref   MED
      Nexthop (Router)                                   Path-Id     Label
      As-Path                                                        
-------------------------------------------------------------------------------
u*>?  1.1.1.2/32                                         100         None
      10.123.121.1                                       1779        131045
      65002                                                           
u*>?  1.1.1.3/32                                         100         145
      192.168.10.1                                       1781        131045
      65002                                                           
u*>?  1.1.2.1/32                                         100         10
      10.20.30.40                                       1894        131
      No As-Path                                                      
u*>?  89.75.232.0/24                                     100         632
      14.191.131.3                                       4           119
      No As-Path                                                      
-------------------------------------------------------------------------------
       """
        parser = routetableBgpTimos.RouteTableBGPTimosParser()
        parser.process(text)
        self.assertEqual( sorted( [("bgp ipv4","1.1.1.2/32","10.123.121.1"), 
                                   ("bgp ipv4","1.1.1.3/32","192.168.10.1"), 
                                   ("bgp ipv4","1.1.2.1/32","10.20.30.40"), 
                                   ("bgp ipv4","89.75.232.0/24","14.191.131.3")] ) , 
                          sorted ( parser.routes_nexthop_protocol("923823") )
                        ) 

                        
    def test_empty_display(self):
        text = """*A:7750# show   router   923823        bgp     routes 
===============================================================================
 BGP Router ID:14.191.131.2     AS:65000       Local AS:65000      
===============================================================================
 Legend -
 Status codes  : u - used, s - suppressed, h - history, d - decayed, * - valid
                 l - leaked, x - stale, > - best, b - backup, p - purge
 Origin codes  : i - IGP, e - EGP, ? - incomplete

===============================================================================
BGP IPv4 Routes
===============================================================================
Flag  Network                                            LocalPref   MED
      Nexthop (Router)                                   Path-Id     Label
      As-Path                                                        
-------------------------------------------------------------------------------
-------------------------------------------------------------------------------
       """ 
        parser = routetableBgpTimos.RouteTableBGPTimosParser()
        parser.process(text)
        self.assertEqual( sorted( [] ) , 
                          sorted ( parser.routes_nexthop_protocol("923823") )
                        )

                        
    def test_one_route(self):
        text = """*A:7750# show   router  12345 bgp     routes 
===============================================================================
 BGP Router ID:14.191.131.2     AS:65000       Local AS:65000      
===============================================================================
 Legend -
 Status codes  : u - used, s - suppressed, h - history, d - decayed, * - valid
                 l - leaked, x - stale, > - best, b - backup, p - purge
 Origin codes  : i - IGP, e - EGP, ? - incomplete

===============================================================================
BGP IPv4 Routes
===============================================================================
Flag  Network                                            LocalPref   MED
      Nexthop (Router)                                   Path-Id     Label
      As-Path                                                        
-------------------------------------------------------------------------------
u*>?  1.1.1.2/32                                         100         None
      14.191.131.3                                       1779        131045
      65002                                                           
-------------------------------------------------------------------------------
       """
        parser = routetableBgpTimos.RouteTableBGPTimosParser()
        parser.process(text)
        self.assertEqual( [("1.1.1.2/32",)] , 
                          parser.routes("12345") 
                        ) 

    def test_status_codes(self):
        text = """*A:7750# show   router  12345 bgp     routes 
===============================================================================
 BGP Router ID:14.191.131.2     AS:65000       Local AS:65000      
===============================================================================
 Legend -
 Status codes  : u - used, s - suppressed, h - history, d - decayed, * - valid
                 l - leaked, x - stale, > - best, b - backup, p - purge
 Origin codes  : i - IGP, e - EGP, ? - incomplete

===============================================================================
BGP IPv4 Routes
===============================================================================
Flag  Network                                            LocalPref   MED
      Nexthop (Router)                                   Path-Id     Label
      As-Path                                                        
-------------------------------------------------------------------------------
ushd*lx>bpie?  1.1.1.2/32                                         100         None
      14.191.131.3                                       1779        131045
      65002                                                           
-------------------------------------------------------------------------------
       """
        parser = routetableBgpTimos.RouteTableBGPTimosParser()
        parser.process(text)
        self.assertEqual( [("1.1.1.2/32",)] , 
                          parser.routes("12345") 
                        ) 

    def test_family(self):
        text = """*A:7750# show   router  bgp     routes    vpn-ipv4
===============================================================================
 BGP Router ID:14.191.131.2     AS:65000       Local AS:65000      
===============================================================================
 Legend -
 Status codes  : u - used, s - suppressed, h - history, d - decayed, * - valid
                 l - leaked, x - stale, > - best, b - backup, p - purge
 Origin codes  : i - IGP, e - EGP, ? - incomplete

===============================================================================
BGP IPv4 Routes
===============================================================================
Flag  Network                                            LocalPref   MED
      Nexthop (Router)                                   Path-Id     Label
      As-Path                                                        
-------------------------------------------------------------------------------
u*>?  10.3.1.2/28                                         100         None
      14.191.131.3                                       1779        131045
      65002                                                           
-------------------------------------------------------------------------------
       """
        parser = routetableBgpTimos.RouteTableBGPTimosParser()
        parser.process(text)
        self.assertEqual( [("bgp vpn-ipv4", "10.3.1.2/28",)] , 
                          parser.routes_protocol("Base") 
                        ) 

    def test_family_vprn(self):
        text = """*A:7750# show   router 123 bgp     routes    vpn-ipv4
===============================================================================
 BGP Router ID:14.191.131.2     AS:65000       Local AS:65000      
===============================================================================
 Legend -
 Status codes  : u - used, s - suppressed, h - history, d - decayed, * - valid
                 l - leaked, x - stale, > - best, b - backup, p - purge
 Origin codes  : i - IGP, e - EGP, ? - incomplete

===============================================================================
BGP IPv4 Routes
===============================================================================
Flag  Network                                            LocalPref   MED
      Nexthop (Router)                                   Path-Id     Label
      As-Path                                                        
-------------------------------------------------------------------------------
u*>?  10.3.1.2/28                                         100         None
      14.191.131.3                                       1779        131045
      65002                                                           
-------------------------------------------------------------------------------
       """
        parser = routetableBgpTimos.RouteTableBGPTimosParser()
        parser.process(text)
        self.assertEqual( [("bgp vpn-ipv4", "10.3.1.2/28",)] , 
                          parser.routes_protocol("123") 
                        ) 

    def test_routes_longASpath_oneline(self):
        text = """*A:7750# show   router  12345 bgp     routes 
===============================================================================
 BGP Router ID:14.191.131.2     AS:65000       Local AS:65000      
===============================================================================
 Legend -
 Status codes  : u - used, s - suppressed, h - history, d - decayed, * - valid
                 l - leaked, x - stale, > - best, b - backup, p - purge
 Origin codes  : i - IGP, e - EGP, ? - incomplete

===============================================================================
BGP IPv4 Routes
===============================================================================
Flag  Network                                            LocalPref   MED
      Nexthop (Router)                                   Path-Id     Label
      As-Path                                                        
-------------------------------------------------------------------------------
*u>?  1.1.1.2/32                                         100         None
      14.191.131.3                                       1779        131045
      65002 65001 65000 65999 65999 65909 6599 60999 5999                     
-------------------------------------------------------------------------------
       """
        parser = routetableBgpTimos.RouteTableBGPTimosParser()
        parser.process(text)
        self.assertEqual( [("1.1.1.2/32",)] , 
                          parser.routes("12345") 
                        ) 

    def test_routes_longASpath_multiline(self):
        text = """*A:7750# show   router  12345 bgp     routes 
===============================================================================
 BGP Router ID:14.191.131.2     AS:65000       Local AS:65000      
===============================================================================
 Legend -
 Status codes  : u - used, s - suppressed, h - history, d - decayed, * - valid
                 l - leaked, x - stale, > - best, b - backup, p - purge
 Origin codes  : i - IGP, e - EGP, ? - incomplete

===============================================================================
BGP IPv4 Routes
===============================================================================
Flag  Network                                            LocalPref   MED
      Nexthop (Router)                                   Path-Id     Label
      As-Path                                                        
-------------------------------------------------------------------------------
*u>?  1.1.1.2/32                                         100         None
      14.191.131.3                                       1779        131045
      65002 65001 65000 65999 65999 65909 6599 60999 5999 1234 12344  
      65002 65001 65000 65999 65999 65909 6599 60999 5999                     
-------------------------------------------------------------------------------
       """
        parser = routetableBgpTimos.RouteTableBGPTimosParser()
        parser.process(text)
        self.assertEqual( [("1.1.1.2/32",)] , 
                          parser.routes("12345") 
                        ) 
                        
    def test_routes_longASpath_multiline_multiroute(self):
        text = """*A:7750# show   router  12345 bgp     routes 
===============================================================================
 BGP Router ID:14.191.131.2     AS:65000       Local AS:65000      
===============================================================================
 Legend -
 Status codes  : u - used, s - suppressed, h - history, d - decayed, * - valid
                 l - leaked, x - stale, > - best, b - backup, p - purge
 Origin codes  : i - IGP, e - EGP, ? - incomplete

===============================================================================
BGP IPv4 Routes
===============================================================================
Flag  Network                                            LocalPref   MED
      Nexthop (Router)                                   Path-Id     Label
      As-Path                                                        
-------------------------------------------------------------------------------
*u>?  1.1.1.2/32                                         100         None
      14.191.131.3                                       1779        131045
      65002 65001 65000 65999 65999 65909 6599 60999 5999 1234 12344  
      65002 65001 65000 65999 65999 65909 6599 60999 5999                     
*u>?  1.1.1.3/32                                         100         None
      14.191.131.3                                       1779        131045
      65002 65001 65000 65999 65999 65909 6599 60999 5999 1234 12344  
      65002 65001 65000 65999 65999 65909 6599 60999 5999                    
-------------------------------------------------------------------------------
       """
        parser = routetableBgpTimos.RouteTableBGPTimosParser()
        parser.process(text)
        self.assertEqual( sorted ( [("1.1.1.2/32",), ("1.1.1.3/32",)] ), 
                          sorted ( list(parser.routes("12345") ) )
                        ) 

    def test_nexthop_noIP(self):
        text = """*A:7750# show   router  12345 bgp     routes 
===============================================================================
 BGP Router ID:14.191.131.2     AS:65000       Local AS:65000      
===============================================================================
 Legend -
 Status codes  : u - used, s - suppressed, h - history, d - decayed, * - valid
                 l - leaked, x - stale, > - best, b - backup, p - purge
 Origin codes  : i - IGP, e - EGP, ? - incomplete

===============================================================================
BGP IPv4 Routes
===============================================================================
Flag  Network                                            LocalPref   MED
      Nexthop (Router)                                   Path-Id     Label
      As-Path                                                        
-------------------------------------------------------------------------------
*u>?  1.1.1.2/32                                         100         None
      999.991.131.3                                       1779        131045
      65002                  
*u>?  1.1.1.3/32                                         100         None
      999.991.131.3                                       1779        131045
      65002          
-------------------------------------------------------------------------------
       """
        parser = routetableBgpTimos.RouteTableBGPTimosParser()
        parser.process(text)
        self.assertEqual( [] , 
                          parser.routes("12345") 
                        ) 

                        
if __name__ == '__main__':
    unittest.main()