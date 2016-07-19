#!python
import routeQuery
from route import *
import renderUtils as ru
from user import *

import random
random.seed()

loc1 = Location(40.536656, -74.489883)
loc2 = Location(40.433534, -74.222451)

rq = routeQuery.RouteQuery()
route = rq.getRoute(loc1,loc2,1200.)
# print route

mroute = route.makeUniformlySampledRoute(1.0)

newRoute = rq.getUniformlySampledRoute(loc1,loc2,1200.0,1.0) 
# print newRoute

rroute = Route()
for i in range(100):
  mroute = newRoute.randomSample(minPercentile=1.0, maxPercentile=10.0)
  mroute.addNoise(noiseSigma=0.001)
  rroute.timedLocations.extend(mroute.timedLocations)

# print rroute
x,y,t = rroute.toLonLatTimeArrays()
# print x

# print Location.distanceInMeters(loc1,loc2)


muser = User()
for i in range(30):
  muser.addTrip(loc1,loc2,secondsSinceLastTrip=11*3600.0,noiseSigma=.004)
  muser.addTrip(loc2,loc1,secondsSinceLastTrip=8*3600.0,noiseSigma=.004)

print muser.errorStatistics()

# ru.renderElement(rroute,alpha=.05)
ru.renderElement(muser,
  withUniform=False,
  withActual=False,
  withMeasured=False,
  withFiltered=True,
  alpha=.1)


