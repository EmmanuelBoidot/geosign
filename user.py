import routeQuery as RQ
from route import *
import copy
import numpy as np

class User:

  def __init__(self):
    self.routes = {}
    self.routes['uniformlySampled'] = Route(timedLocations=[])
    self.routes['measured'] = Route(timedLocations=[])
    self.routes['actual'] = Route(timedLocations=[])
    self.routes['filtered'] = Route(timedLocations=[])
    self.signature = {}
    self.errors = {}
    self.errors['measured'] = []
    self.errors['filtered'] = []

  def addTrip(self,dep_location,arr_location,sampling_period_in_sec=1.0,
      secondsSinceLastTrip=0.0,noiseSigma=.005,
      minPercentile=.001,maxPercentile=0.1,
      API='OSRM'):

    lastTimestamp = secondsSinceLastTrip
    lastTimestamp += 0 if len(self.routes['uniformlySampled'].timedLocations)==0 else \
      self.routes['uniformlySampled'].timedLocations[-1].timestamp

    # get exact route with time origin larger than last timestamp
    if API=='Google':
      rq = RQ.GoogleRouteQuery()
    else:
      rq = RQ.OSRMRouteQuery()
    newRoute = rq.getUniformlySampledRoute(dep_location,
      arr_location,lastTimestamp,sampling_period_in_sec)
    self.routes['uniformlySampled'].extend(newRoute)

    # sample only a subset of this new route as actual location
    sroute = newRoute.randomSample(minPercentile=minPercentile,
        maxPercentile=maxPercentile)
    self.routes['actual'].extend(sroute)
    
    nroute = copy.deepcopy(sroute)
    nroute.addNoise(noiseSigma)
    self.routes['measured'].extend(nroute)
    self.errors['measured'].extend(nroute.arrayDistanceInMeters(sroute))

    # TODO: change this to actual filtered signal
    froute = copy.deepcopy(nroute)
    self.routes['filtered'].extend(froute)
    self.errors['filtered'].extend(froute.arrayDistanceInMeters(sroute))
    return


  def getSignal(self,signal):
    try:
      a = self.routes[signal].timedLocations
    except KeyError:
      print("signal must be either 'uniformlySampled','measured','actual' or 'filtered'")
      a = []

    return a


  def toLonLatTimeArrays(self,signal='uniformlySampled'):
    a = self.getSignal(signal)

    x = [tl.location.lon for tl in a]
    y = [tl.location.lat for tl in a]
    t = [tl.timestamp for tl in a]
    return x,y,t


  def getErrorStatistics(self,signal,numBins=10):
    try:
      errors = self.errors[signal]
    except KeyError:
      print("errors must be either 'measured' or 'filtered'")
      errors = []
    return np.histogram(errors,bins=numBins)


  def computeErrors(self,signal):
    a = self.getSignal(signal)
    b = self.getSignal('actual')
    return TimedLocation.arrayDistanceInMeters(a,b)


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
    hm = self.routes['measured'].toHeatmap()
    hm.bilateral_sharpen(maxDistance)
    self.routes['filtered'].timedLocations = self.routes['measured'].filterFromHeatmap(hm,
        maxDistance,heatThreshold)
    self.errors_filtered = self.computeErrors('filtered')