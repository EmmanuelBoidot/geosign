import routeQuery as RQ
from route import *
import copy
import numpy as np

class User:

  def __init__(self):
    self.route_uniformlySampled = Route()
    self.route_measured = Route()
    self.route_actual = Route()
    self.route_filtered = Route()
    self.signature = {}
    self.errors_measured = []
    self.errors_filtered = []

  def addTrip(self,dep_location,arr_location,sampling_period_in_sec=1.0,
      secondsSinceLastTrip=0.0,noiseSigma=.005):
    lastTimestamp = secondsSinceLastTrip
    lastTimestamp += 0 if len(self.route_uniformlySampled.timedLocations)==0 else \
      self.route_uniformlySampled.timedLocations[-1].timestamp

    # get exact route with time origin larger than last timestamp
    rq = RQ.RouteQuery()
    newRoute = rq.getUniformlySampledRoute(dep_location,
      arr_location,lastTimestamp,sampling_period_in_sec)


    # sample only a subset of this new route as actual location
    sroute = newRoute.randomSample(minPercentile=1.0,maxPercentile=10.0)

    self.route_uniformlySampled.timedLocations.extend(newRoute.timedLocations)
    self.route_actual.timedLocations.extend(copy.deepcopy(sroute.timedLocations))
    sroute.addNoise(noiseSigma)
    self.route_measured.timedLocations.extend(sroute.timedLocations)
    self.errors_measured = self.computeErrors('measured')

    # TODO: change this to actual filtered signal
    self.route_filtered.timedLocations.extend(sroute.timedLocations)
    self.errors_filtered = self.computeErrors('filtered')
    return

  def toLonLatTimeArrays(self,signal='uniformlySampled'):
    a = self.route_uniformlySampled.timedLocations
    if signal=='measured':
      a = self.route_measured.timedLocations
    elif signal=='actual':
      a = self.route_actual.timedLocations
    elif signal=='filtered':
      a = self.route_filtered.timedLocations

    x = [tl.location.lon for tl in a]
    y = [tl.location.lat for tl in a]
    t = [tl.timestamp for tl in a]
    return x,y,t

  def errorStatistics(self,signal,numBins=10):
    errors = self.computeErrors(signal)
    return np.histogram(errors,bins=numBins)

  def computeErrors(self,signal):
    if signal=='measured':
      a = self.route_measured.timedLocations
    elif signal=='filtered':
      a = self.route_filtered.timedLocations

    return [Location.distanceInMeters(
                self.route_actual.timedLocations[i].location,
                a[i].location
                )
              for i in range(len(self.route_actual.timedLocations))]


  def render(self,ax,withUniform=True,withActual=True,withMeasured=True,
      withFiltered=True,**kwargs):
    if kwargs.has_key('c'):
      del kwargs['c']

    kwargs['marker'] = '^' if not kwargs.has_key('marker') else kwargs['marker']
    kwargs['alpha'] = .05 if not kwargs.has_key('alpha') else kwargs['alpha']
    
    if withUniform:
      x1,y1,t1 = self.toLonLatTimeArrays('uniformlySampled')
      kwargs['s'] = [10]*len(x1)
      ax.scatter(x1, y1, c='k',**kwargs)

    if withActual:
      x2,y2,t2 = self.toLonLatTimeArrays('actual')
      kwargs['s'] = [20]*len(x2)
      ax.scatter(x2, y2, c='b',**kwargs)

    if withMeasured:
      x3,y3,t3 = self.toLonLatTimeArrays('measured')
      kwargs['s'] = [20]*len(x3)
      ax.scatter(x3, y3, c='r',**kwargs)

    if withFiltered:
      x4,y4,t4 = self.toLonLatTimeArrays('filtered')
      kwargs['s'] = [20]*len(x4)
      ax.scatter(x4, y4, c='g',**kwargs)

  def bilateralFilter(self,maxDistance=5,heatThreshold=.01):
    hm = self.route_measured.toHeatmap()
    hm.bilateral_sharpen(maxDistance)
    self.route_filtered.timedLocations = self.route_measured.filterFromHeatmap(hm,
        maxDistance,heatThreshold)
    self.errors_filtered = self.computeErrors('filtered')