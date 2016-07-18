import routeQuery as RQ
from route import *
import copy
import numpy as np

class User:

  def __init__(self):
    self.timedLocations_uniformlySampled = []
    self.timedLocations_measured = []
    self.timedLocations_actual = []
    self.timedLocations_filtered = []
    self.signature = {}

  def addTrip(self,dep_location,arr_location,sampling_period_in_sec=1.0,
      noiseSigma=.005):
    lastTimestamp = 0 if len(self.timedLocations_uniformlySampled)==0 else \
      self.timedLocations_uniformlySampled[-1] 
    # get exact route with time origin larger than last timestamp
    rq = RQ.RouteQuery()
    newRoute = rq.getUniformlySampledRoute(dep_location,
      arr_location,lastTimestamp,sampling_period_in_sec)


    # sample only a subset of this new route as actual location
    sroute = newRoute.randomSample(minPercentile=1.0,maxPercentile=10.0)

    self.timedLocations_uniformlySampled.extend(newRoute.timedLocations)
    self.timedLocations_actual.extend(copy.deepcopy(sroute.timedLocations))
    sroute.addNoise(noiseSigma)
    self.timedLocations_measured.extend(sroute.timedLocations)

    # TODO: change this to actual filtered signal
    self.timedLocations_filtered.extend(sroute.timedLocations)
    return

  def toLonLatTimeArrays(self,signal='uniformlySampled'):
    a = self.timedLocations_uniformlySampled
    if signal=='measured':
      a = self.timedLocations_measured
    elif signal=='actual':
      a = self.timedLocations_actual
    elif signal=='filtered':
      a = self.timedLocations_filtered

    x = [tl.location.lon for tl in a]
    y = [tl.location.lat for tl in a]
    t = [tl.timestamp for tl in a]
    return x,y,t

  def errorStatistics(self,numBins=10):
    errors = [Location.distanceInMeters(
                self.timedLocations_actual[i].location,
                self.timedLocations_measured[i].location
                )
              for i in range(len(self.timedLocations_actual))]
    return np.histogram(errors,bins=numBins)

  def render(self,ax,**kwargs):
    if kwargs.has_key('c'):
      del kwargs['c']

    kwargs['marker'] = 'o' if not kwargs.has_key('marker') else kwargs['marker']
    kwargs['alpha'] = .05 if not kwargs.has_key('alpha') else kwargs['alpha']
    kwargs['linewidths'] = \
        0 if not kwargs.has_key('linewidths') else kwargs['linewidths']
    
    x1,y1,t1 = self.toLonLatTimeArrays('uniformlySampled')
    kwargs['s'] = [10]*len(x1)
    ax.scatter(x1, y1, c='k',**kwargs)

    x2,y2,t2 = self.toLonLatTimeArrays('actual')
    kwargs['s'] = [20]*len(x2)
    ax.scatter(x2, y2, c='b',**kwargs)

    x3,y3,t3 = self.toLonLatTimeArrays('measured')
    kwargs['s'] = [20]*len(x3)
    ax.scatter(x3, y3, c='r',**kwargs)