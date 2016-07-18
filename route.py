class Route:

  ###
  # !!! Highly dependent on the datastructure retuned by OSRM server
  #
  ###
  def __init__(self, steps=[],firstTimestamp=0.0):
    self.timedLocations = []

    if len(steps)==0:
      return

    prevTimestamp = firstTimestamp
    tl = TimedLocation(
            steps[0]['geometry']['coordinates'][0][1],
            steps[0]['geometry']['coordinates'][0][0],
            prevTimestamp
          )
    self.timedLocations.append(tl)

    for s in steps: # should be using 'geometry' instead
      timedLocs = TimedLocation.makeTimedLocationFromCoordinatesAndTotalDuration(
                    s['geometry']['coordinates'],
                    s['duration'],
                    prevTimestamp
                  )
      self.timedLocations.extend(timedLocs)
      prevTimestamp += s['duration']

  def __str__(self):
    return self.toString()

  def appendPoint(self,lat,lon,timestamp):
    self.timedLocations.append(TimedLocation(lat,lon,timestamp))
    return

  def makeUniformlySampledRoute(self,sampling_period_in_sec=1.0):
    mroute = Route()
    if len(self.timedLocations)==0:
      return mroute

    lat0 = self.timedLocations[0].location.lat
    lon0 = self.timedLocations[0].location.lon
    firstTimestamp = \
      int(self.timedLocations[0].timestamp/sampling_period_in_sec)*sampling_period_in_sec
    totalDurationInSeconds = self.timedLocations[-1].timestamp-firstTimestamp
    numberOfPoints = int(totalDurationInSeconds/sampling_period_in_sec)+1

    mroute.timedLocations = \
      [TimedLocation(lat0,lon0,sampling_period_in_sec*i+firstTimestamp) for i 
        in range(numberOfPoints+1)]

    self_tl_idx = 1
    for tl in mroute.timedLocations[1:]:
      while (self_tl_idx<len(self.timedLocations) and 
              self.timedLocations[self_tl_idx].timestamp<tl.timestamp):
        self_tl_idx+=1
      if not (self_tl_idx<len(self.timedLocations)):
        break

      tl1 = self.timedLocations[self_tl_idx-1]
      tl2 = self.timedLocations[self_tl_idx]
      try:
        ratio = (tl.timestamp-tl1.timestamp)/(tl2.timestamp-tl1.timestamp)
      except ZeroDivisionError as e:
        print e
        print tl1.toString()+"\t"+tl2.toString()


      tl.location = Location.intermediatePoint(tl1.location,tl2.location,ratio)

    mroute.timedLocations[-1].location = self.timedLocations[-1].location

    return mroute

  def toLonLatArrays(self):
    X = [tl.location.lon for tl in self.timedLocations]
    Y = [tl.location.lat for tl in self.timedLocations]
    return X,Y

  def toLatLonTimeArrays(self):
    X,Y = self.toLonLatArrays()
    return Y,X

  def toLonLatTimeArrays(self):
    X,Y = self.toLonLatArrays()
    T = [tl.timestamp for tl in self.timedLocations]
    return X,Y,T

  def toLatLonTimeArrays(self):
    X,Y = self.toLatLonArrays()
    T = [tl.timestamp for tl in self.timedLocations]
    return X,Y,T

  def toString(self):
    return ",".join([tl.toString() for tl in self.timedLocations])

  def checkTimeValidity(self):
    for tli in range(len(route.timedLocations)-1):
      if (route.timedLocations[tli].timestamp>route.timedLocations[tli+1].timestamp):
          print route.timedLocations[tli].toString()+"\t"+route.timedLocations[tli+1].toString()
          return false
    return True

  def randomSample(self,minPercentile=1.0,maxPercentile=20.0):
    numPoints = len(self.timedLocations)
    mroute = Route()
    if numPoints==0:
      return mroute
    
    # takes between minPercentile % and maxPercentile % of all points
    numPointsToSample = random.randrange(int(numPoints*minPercentile/100),
                                        int(numPoints*maxPercentile/100))
    pointIndices = geomUtils.selectKItems(numPoints,numPointsToSample)
    mroute.timedLocations = [self.timedLocations[i] for i in pointIndices]
    return mroute

  def addNoise(self,noiseSigma=.005): # noise is in degrees (latitude,longitude)
    for tl in self.timedLocations:
      tl.location.addNoise(noiseSigma)

  def render(self,ax,**kwargs):
    x,y,t = self.toLonLatTimeArrays()

    kwargs['marker'] = 'o' if not kwargs.has_key('marker') else kwargs['marker']
    kwargs['s'] = [10]*len(x) if not kwargs.has_key('s') else kwargs['s']
    # kwargs['cmap'] = \
    #     plt.get_cmap('winter') if not kwargs.has_key('cmap') else kwargs['cmap']
    kwargs['c'] = 'b' if not kwargs.has_key('c') else kwargs['c']
    kwargs['alpha'] = .01 if not kwargs.has_key('alpha') else kwargs['alpha']
    kwargs['linewidths'] = \
        0 if not kwargs.has_key('linewidths') else kwargs['linewidths']
      
    ax.scatter(x, y, **kwargs)


class UniformlySampledRoute(Route):

  def __init__(self, steps=[],firstTimestamp=0.0,sampling_period_in_sec=1.0):
    Route.__init__(self,steps,firstTimestamp=firstTimestamp)
    self.timedLocations = \
      self.makeUniformlySampledRoute(sampling_period_in_sec).timedLocations
    self.sampling_period_in_sec = sampling_period_in_sec


class TimedLocation:

  def __init__(self,lat,lon,timestamp):
    self.location = Location(lat,lon)
    self.timestamp = timestamp

  def __str__(self):
    return self.toString()

  def toString(self):
    return "[%f: %s]"%(self.timestamp,self.location.toString())

  @staticmethod
  def makeTimedLocationFromCoordinatesAndTotalDuration(lonlats,totalDuration,
      prevTimestamp=0.0):

    timedLocs = [TimedLocation(ss[1], ss[0], prevTimestamp) for ss in lonlats]
    distances = [0.0]*len(lonlats)
    # for each intermediary point on the segment, compute the timestamp associated 
    # by doing a distance ratio. Assumes constant speed on segment.
    for i in range(1,len(lonlats)):
      distances[i] = Location.distanceInMeters(timedLocs[i-1].location,
                                                timedLocs[i].location)

    totalDistance = sum(distances)
    for i in range(1,len(lonlats)):
      timedLocs[i].timestamp = totalDuration*distances[i]/totalDistance\
                                  +timedLocs[i-1].timestamp

    return timedLocs[1:]
      

import geopy.distance
import random
import geomUtils

class Location:

  def __init__(self,lat,lon):
    self.lat = lat
    self.lon = lon

  def __str__(self):
    return self.toString()

  def toLatLonString(self):
    return "%f,%f"%self.toLatLonTuple()

  def toLonLatString(self):
    return "%f,%f"%self.toLonLatTuple()

  def toLatLonTuple(self):
    return (self.lat,self.lon)

  def toLonLatTuple(self):
    return (self.lon,self.lat)

  def toString(self):
    return "(%s)"%(self.toLatLonString())

  def addNoise(self,noiseSigma=.005):
    self.lat += random.gauss(0.0,noiseSigma)
    self.lon += random.gauss(0.0,noiseSigma)

  @staticmethod
  def distanceInMeters(location1,location2):
    return geopy.distance.distance(
      location1.toLatLonTuple(),
      location2.toLatLonTuple()
    ).meters

  @staticmethod
  def intermediatePoint(location1,location2,ratio):
    lat = location1.lat+ratio*(location2.lat-location1.lat)
    lon = location1.lon+ratio*(location2.lon-location1.lon)
    return Location(lat,lon)
