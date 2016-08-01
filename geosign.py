#!python
import copy
from threading import Thread

import routeQuery
from route import *
import renderUtils as ru
from heatmap import *
from user import *

import random
random.seed()

mAPI = 'Google'
rq = routeQuery.GoogleRouteQuery() if mAPI=='Google' else routeQuery.OSRMRouteQuery()

loc1 = Location(40.536656,-74.489883)
loc2 = Location(40.433534,-74.222451)

print loc1.toGeohash(7)

route = rq.getRoute(loc1,loc2,1200.)
# print route

mroute = route.makeUniformlySampledRoute(1.0)

newRoute = rq.getUniformlySampledRoute(loc1,loc2,1200.0,1.0) 
# print newRoute

rroute = Route()
# for i in range(100):
#   mroute = newRoute.randomSample(minPercentile=1.0, maxPercentile=10.0)
#   mroute.addNoise(noiseSigma=0.001)
#   rroute.timedLocations.extend(mroute.timedLocations)

hmap = mroute.toHeatmap(7)
# ru.renderElement(hmap)
# plt.show()

# print rroute
x,y,t = rroute.toLonLatTimeArrays()
# print x

# print Location.distanceInMeters(loc1,loc2)

args = {'sampling_period_in_sec':1.0,
'secondsSinceLastTrip':11*3600.0,'noiseSigma':.004,
'minPercentile':.001,'maxPercentile':.05,'API':mAPI}

muser = User()
for i in range(10):
  print('Day %d:'%(i))
  muser.addTrip(loc1,loc2, **args)
  muser.addTrip(loc2,loc1, **args)

print muser.getErrorStatistics('measured')
print muser.getErrorStatistics('filtered')

hm = muser.routes['measured'].toHeatmap(geohashlength=8)
hm2 = copy.deepcopy(hm)
hm2.normalize()

hm3 = hm2.computeBilateralFilteredHeatmap(maxdist=2)

hm4 = hm2.bilateral_sharpen(maxdist=2)
hm4 = hm4.bilateral_sharpen(maxdist=2)
hm4 = hm4.bilateral_sharpen(maxdist=2)
hm4.filterOutExtrema(0.45,10)

# ru.renderElements([hm],usePyLeaflet=False)
# ru.renderElements([hm2],usePyLeaflet=False,logScale=False)
# ru.renderElements([hm3],usePyLeaflet=False,logScale=False)
# ru.renderElements([hm4],usePyLeaflet=False,logScale=False,colormapname='nothingRed')
# plt.show()

# ru.renderElements([hm4,muser.routes['measured']],usePyLeaflet=True,alpha=.6)


mgraph = hm4.toGraph()
mtree = mgraph.kruskal()
ru.renderElements([mtree,muser.routes['measured']],usePyLeaflet=True)

# muser.bilateralFilter()

# ru.renderUser(muser,usePyLeaflet=True)

# ru.renderElements([muser.routes['measured']],usePyLeaflet=True,alpha=.8)

# # ru.renderElements(rroute,alpha=.05)
# ru.renderElements(muser,
#   withUniform=False,
#   withActual=False,
#   withMeasured=False,
#   withFiltered=True,
#   alpha=.1)


