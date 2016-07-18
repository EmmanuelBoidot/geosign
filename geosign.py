#!python
from routeQuery import *
import renderUtils as ru

import random
random.seed()

rq = RouteQuery()
route = rq.getRoute(Location(40.536656, -74.489883),Location(40.433534, -74.222451))
# print route.toString()

mroute = route.makeUniformlySampledRoute(1.0)

newRoute = rq.getUniformlySampledRoute(Location(40.536656, -74.489883),
                                        Location(40.433534, -74.222451),1.0) 

rroute = Route()
for i in range(100):
  rroute.timedLocations.extend(newRoute.randomSample(noiseSigma=0.001,
    minPercentile=1.0,maxPercentile=10.0).timedLocations)

# print rroute
x,y,t = rroute.toLonLatTimeArrays()
# print x

# print Location.distanceInMeters(Location(40.536656, -74.489883),Location(40.536656, -74.484883))
ru.renderRoute(rroute,alpha=.05)



