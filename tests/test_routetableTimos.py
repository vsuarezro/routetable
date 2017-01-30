import os
import sys
sys.path.insert(0, os.path.abspath('..'))

import unittest
from parsers import routetableTimos


class TestParserTimos(unittest.TestCase):
    
    def test_routersID(self):
        text = """*A:7750>config>service>vprn$ show router 99 route-table 

===============================================================================
Route Table (Service: 99)
===============================================================================
Dest Prefix[Flags]                            Type    Proto     Age        Pref
      Next Hop[Interface Name]                                    Metric   
-------------------------------------------------------------------------------
1.1.1.2/32                                    Local   Local     76d07h31m  0
       loop-1                                                       0
-------------------------------------------------------------------------------
       """
        parser = routetableTimos.RouteTableTimosParser()
        parser.process(text)
        self.assertEqual( ["99"] , list(parser.routersID()) )
    
    def test_routersID_base(self):
        text = """*A:7750>config>service>vprn$ show router route-table 

===============================================================================
Route Table (Service: Base)
===============================================================================
Dest Prefix[Flags]                            Type    Proto     Age        Pref
      Next Hop[Interface Name]                                    Metric   
-------------------------------------------------------------------------------
1.1.1.2/32                                    Local   Local     76d07h31m  0
       loop-1                                                       0
-------------------------------------------------------------------------------
       """
        parser = routetableTimos.RouteTableTimosParser()
        parser.process(text)
        self.assertEqual( ["Base"] , list(parser.routersID()) )
       
    def test_no_routerID(self):
        text = """*A:7750$       show      router 12345        route-table 

===============================================================================
Route Table (Service: 12345)
===============================================================================
Dest Prefix[Flags]                            Type    Proto     Age        Pref
      Next Hop[Interface Name]                                    Metric   
-------------------------------------------------------------------------------
1.1.1.2/32                                    Local   Local     76d07h31m  0
       loop-1                                                       0
-------------------------------------------------------------------------------
       """
        parser = routetableTimos.RouteTableTimosParser()
        parser.process(text)
        self.assertEqual( ["12345"] , list(parser.routersID()) )

    def test_multiple_tables(self):
        text = """*A:7750$       show      router 12345        route-table 

===============================================================================
Route Table (Service: 12345)
===============================================================================
Dest Prefix[Flags]                            Type    Proto     Age        Pref
      Next Hop[Interface Name]                                    Metric   
-------------------------------------------------------------------------------
1.1.1.2/32                                    Local   Local     76d07h31m  0
       loop-1                                                       0
-------------------------------------------------------------------------------
*A:7750$       show      router      43214321        route-table 

===============================================================================
Route Table (Service: 43214321)
===============================================================================
Dest Prefix[Flags]                            Type    Proto     Age        Pref
      Next Hop[Interface Name]                                    Metric   
-------------------------------------------------------------------------------
-------------------------------------------------------------------------------
*A:7750$       show      router                route-table 

===============================================================================
Route Table (Service: Base)
===============================================================================
Dest Prefix[Flags]                            Type    Proto     Age        Pref
      Next Hop[Interface Name]                                    Metric   
-------------------------------------------------------------------------------
1.1.1.2/32                                    Local   Local     76d07h31m  0
       loop-1                                                       0
-------------------------------------------------------------------------------

       """    
        parser = routetableTimos.RouteTableTimosParser()
        parser.process(text)
        self.assertEqual( sorted(["12345", "43214321", "Base"]) , sorted(list(parser.routersID())) ) 
    
    def test_one_route(self):
        text = """*A:7750$       show      router 12345        route-table 

===============================================================================
Route Table (Service: 12345)
===============================================================================
Dest Prefix[Flags]                            Type    Proto     Age        Pref
      Next Hop[Interface Name]                                    Metric   
-------------------------------------------------------------------------------
1.1.1.2/32                                    Local   Local     76d07h31m  0
       loop-1                                                       0
-------------------------------------------------------------------------------
       """    
        parser = routetableTimos.RouteTableTimosParser()
        parser.process(text)
        self.assertEqual( [("1.1.1.2/32",)] , 
                          parser.routes("12345") 
                        ) 
    
    def test_one_route_nexthop(self):
        text = """*A:7750$       show  router 999        route-table 

===============================================================================
Route Table (Service: 999)
===============================================================================
Dest Prefix[Flags]                            Type    Proto     Age        Pref
      Next Hop[Interface Name]                                    Metric   
-------------------------------------------------------------------------------
1.1.1.2/32                                    Local   Local     76d07h31m  0
       loop-1                                                       0
-------------------------------------------------------------------------------
       """    
        parser = routetableTimos.RouteTableTimosParser()
        parser.process(text)
        self.assertEqual( [("1.1.1.2/32","loop-1",)] , 
                          parser.routes_nexthop("999") 
                        ) 
    
    def test_route_protocol(self):
        text = """*A:7750$       show  router      route-table 

===============================================================================
Route Table (Service: Base)
===============================================================================
Dest Prefix[Flags]                            Type    Proto     Age        Pref
      Next Hop[Interface Name]                                    Metric   
-------------------------------------------------------------------------------
1.1.2.3/32                                    Remote  BGP       14d07h27m  170
       14.191.131.3 (tunneled:RSVP:2)                               0
-------------------------------------------------------------------------------
       """    
        parser = routetableTimos.RouteTableTimosParser()
        parser.process(text)
        self.assertEqual( [("BGP","1.1.2.3/32",)] , 
                          parser.routes_protocol("Base") 
                        ) 
    
    def test_route_protocol(self):
        text = """*A:7750$       show  router      route-table 

===============================================================================
Route Table (Service: Base)
===============================================================================
Dest Prefix[Flags]                            Type    Proto     Age        Pref
      Next Hop[Interface Name]                                    Metric   
-------------------------------------------------------------------------------
1.1.2.3/32                                    Remote  BGP       14d07h27m  170
       14.191.131.3 (tunneled:RSVP:2)                               0
-------------------------------------------------------------------------------
       """    
        parser = routetableTimos.RouteTableTimosParser()
        parser.process(text)
        self.assertEqual( [("BGP","1.1.2.3/32","14.191.131.3")] ,
                          parser.routes_nexthop_protocol("Base") 
                        ) 
    
    def test_multiple_routes(self):
        text = """*A:7750$       show      router 12345        route-table 

===============================================================================
Route Table (Service: 12345)
===============================================================================
Dest Prefix[Flags]                            Type    Proto     Age        Pref
      Next Hop[Interface Name]                                    Metric   
-------------------------------------------------------------------------------
1.1.1.2/32                                    Local   Local     76d07h31m  0
       loop-1                                                       0
1.1.1.3/32                                    Remote  BGP       14d07h27m  170
       14.191.131.3 (tunneled:RSVP:2)                               0
1.1.2.1/32                                    Remote  ISIS      38d19h02m  18
       14.191.131.118                                               10
10.10.10.1/32                                 Blackh* Static    00h01m22s  5
       Black Hole                                                   1
-------------------------------------------------------------------------------
       """    
        parser = routetableTimos.RouteTableTimosParser()
        parser.process(text)
        self.assertEqual( sorted( [("1.1.1.2/32",), ("1.1.1.3/32",), ("1.1.2.1/32",), ("10.10.10.1/32",)] ) , 
                          sorted ( parser.routes("12345") )
                        ) 
    
    def test_multiple_routes_nexthop_protocol(self):
        text = """*A:7750$       show      router 12345        route-table 

===============================================================================
Route Table (Service: 12345)
===============================================================================
Dest Prefix[Flags]                            Type    Proto     Age        Pref
      Next Hop[Interface Name]                                    Metric   
-------------------------------------------------------------------------------
1.1.1.2/32                                    Local   Local     76d07h31m  0
       loop-1                                                       0
1.1.1.3/32                                    Remote  BGP       14d07h27m  170
       14.191.131.3 (tunneled:RSVP:2)                               0
1.1.2.1/32                                    Remote  ISIS      38d19h02m  18
       14.191.131.118                                               10
10.10.10.1/32                                 Blackh* Static    00h01m22s  5
       Black Hole                                                   1
-------------------------------------------------------------------------------
       """    
        parser = routetableTimos.RouteTableTimosParser()
        parser.process(text)
        self.assertEqual( sorted( [("Local","1.1.1.2/32","loop-1"), 
                                   ("BGP","1.1.1.3/32","14.191.131.3"), 
                                   ("ISIS","1.1.2.1/32","14.191.131.118"), 
                                   ("Static","10.10.10.1/32","Black Hole")] ) , 
                          sorted ( parser.routes_nexthop_protocol("12345") )
                        ) 

    def test_wrong_display(self):
        text = """*A:7750$       show      router 11111 route-table 

===============================================================================
Route Table (Service: Base)
===============================================================================
Dest Prefix[Flags]                            Type    Proto     Age        Pref
      Next Hop[Interface Name]                                    Metric   
-------------------------------------------------------------------------------
1.1.1.2/32                                    Local   Local     76d07h31m  0
       loop-1                                                       0
1.1.1.3/32                                    Remote  BGP       14d07h27m  170
       14.191.131.3 (tunneled:RSVP:2)                               0
1.1.2.1/32                                    Remote  ISIS      38d19h02m  18
       14.191.131.118                                               10
10.10.10.1/32                                 Blackh* Static    00h01m22s  5
       Black Hole                                                   1
-------------------------------------------------------------------------------
       """    
        parser = routetableTimos.RouteTableTimosParser()
        parser.process(text)
        self.assertEqual( sorted( [] ) , 
                          sorted ( parser.routes_nexthop_protocol("11111") )
                        )
                        
    def test_empty_display(self):
        text = """*A:7750$       show      router 11111 route-table 

===============================================================================
Route Table (Service: Base)
===============================================================================
Dest Prefix[Flags]                            Type    Proto     Age        Pref
      Next Hop[Interface Name]                                    Metric   
-------------------------------------------------------------------------------
-------------------------------------------------------------------------------
       """    
        parser = routetableTimos.RouteTableTimosParser()
        parser.process(text)
        self.assertEqual( sorted( [] ) , 
                          sorted ( parser.routes_nexthop_protocol("11111") )
                        )
                        
    def test_black_hole_nexthop(self):
        text = """*A:7750$       show      router 11111 route-table 

===============================================================================
Route Table (Service: 11111)
===============================================================================
Dest Prefix[Flags]                            Type    Proto     Age        Pref
      Next Hop[Interface Name]                                    Metric   
-------------------------------------------------------------------------------
10.10.10.1/32                                 Blackh* Static    00h01m22s  5
       Black Hole                                                   1
10.10.10.2/32                                 Blackh* Static    00h01m22s  5
       Black Hole                                                   1
-------------------------------------------------------------------------------
       """    
        parser = routetableTimos.RouteTableTimosParser()
        parser.process(text)
        self.assertEqual( sorted( [("Static","10.10.10.1/32","Black Hole"), 
                                   ("Static","10.10.10.2/32","Black Hole")] ) , 
                          sorted ( parser.routes_nexthop_protocol("11111") )
                        ) 

    
    
    
if __name__ == '__main__':
    unittest.main()