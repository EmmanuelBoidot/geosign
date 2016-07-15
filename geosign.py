#!python
from routeQuery import *
import renderUtils as ru

rq = RouteQuery()
route = rq.getRoute(Location(40.536656, -74.489883),Location(40.433534, -74.222451))
# print route.toString()

mroute = route.makeUniformlySampledRoute(2.0)

newRoute = rq.getUniformlySampledRoute(Location(40.536656, -74.489883),Location(40.433534, -74.222451),60.0) 


ru.renderRoute(newRoute)





