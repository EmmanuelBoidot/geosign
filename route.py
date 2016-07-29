import copy
import sys

import geomUtils as gu
from heatmap import *

class Route:

  ###
  # !!! Highly dependent on the datastructure retuned by OSRM server
  #
  ###
  def __init__(self, timedLocations=[]):
    self.timedLocations = timedLocations

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

  def extend(self,other):
    self.timedLocations.extend(other.timedLocations)

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

  def randomSample(self,minPercentile=.01,maxPercentile=.2):
    numPoints = len(self.timedLocations)
    mroute = Route()
    if numPoints==0:
      return mroute
    
    # takes between minPercentile % and maxPercentile % of all points
    numPointsToSample = random.randrange(int(numPoints*minPercentile),
                max(int(numPoints*minPercentile)+1,int(numPoints*maxPercentile)))
    pointIndices = geomUtils.selectKItems(numPoints,numPointsToSample)
    mroute.timedLocations = [self.timedLocations[i] for i in pointIndices]
    return mroute

  def addNoise(self,noiseSigma=.005): # noise is in degrees (latitude,longitude)
    for tl in self.timedLocations:
      tl.location.addNoise(noiseSigma)

  def render(self,ax,**kwargs):
    x,y,t = self.toLonLatTimeArrays()

    kwargs['marker'] = '^' if not kwargs.has_key('marker') else kwargs['marker']
    kwargs['s'] = [10]*len(x) if not kwargs.has_key('s') else kwargs['s']
    # kwargs['cmap'] = \
    #     plt.get_cmap('winter') if not kwargs.has_key('cmap') else kwargs['cmap']
    kwargs['c'] = 'b' if not kwargs.has_key('c') else kwargs['c']
    kwargs['alpha'] = .7 if not kwargs.has_key('alpha') else kwargs['alpha']
    kwargs['linewidths'] = \
        0 if not kwargs.has_key('linewidths') else kwargs['linewidths']
      
    ax.scatter(x, y, **kwargs)

  def toHeatmap(self, geohashlength=7, maxInterpolationTimeInterval=300,
      maxInterpolationDistance=1000, numIntermediatePoints=10):
    # 1. first, we should aggregate static data in a meaningful manner... maybe?
    # the user signature is more reliable on more dynamic data

    # 2. populate timeserie with intermediary geohashes
    # then get heatmap
    hmap = {'maxvalue':0,
            'minvalue':sys.maxint,
            'geohashlength':geohashlength,
            'minlat': 180.,
            'maxlat': -180.,
            'minlon': 180.,
            'maxlon': -180.
            }
    if len(self.timedLocations)==0:
      return Heatmap(hmap)

    prevTimedLoc = self.timedLocations[0]
    hmap[prevTimedLoc.toGeohash(geohashlength)] = 1
    for k in range(1,len(self.timedLocations)):
      # if the two points are too far away distance-wise or timewise, don't interpolate
      if (self.timedLocations[k].timestamp-prevTimedLoc.timestamp)>maxInterpolationTimeInterval or Location.distanceInMeters(self.timedLocations[k],prevTimedLoc)>maxInterpolationDistance:
        hashes = [prevTimedLoc.toGeohash(geohashlength)]
        # TODO: instead of distance=2, should take estimated error into account
        # and translate it into geohash distance
        hashes.extend(gu.geohashNeighbors(hashes[0],2))
        for h in hashes:
          if h in hmap:
            hmap[h]+=1
            hmap['maxvalue'] = max(hmap['maxvalue'],hmap[h])
            hmap['minvalue'] = min(hmap['minvalue'],hmap[h])
          else:
            hmap[h]=1.0
      else:
        i=0
        while (i<numIntermediatePoints):
          prevTimedLoc = self.timedLocations[k-1].intermediatePointTo(
              self.timedLocations[k],(1.0*i)/numIntermediatePoints)

          h = prevTimedLoc.toGeohash(geohashlength)
          if h in hmap:
            hmap[h]+=1
            hmap['maxvalue'] = max(hmap['maxvalue'],hmap[h])
            hmap['minvalue'] = min(hmap['minvalue'],hmap[h])
          else:
            hmap[h]=1
          i+=1

      hmap['minlon'] = min(hmap['minlon'], self.timedLocations[k].location.lon)
      hmap['minlat'] = min(hmap['minlat'], self.timedLocations[k].location.lat)
      hmap['maxlon'] = max(hmap['maxlon'], self.timedLocations[k].location.lon)
      hmap['maxlat'] = max(hmap['maxlat'], self.timedLocations[k].location.lat)

      prevTimedLoc = self.timedLocations[k]

    # 3.
    return Heatmap(hmap)

  def filterFromHeatmap(self,hmap,maxDistance=5,heatThreshold=.01):
    data = self.timedLocations
    ndata = copy.deepcopy(data)
    geohashlength = hmap.geohashlength
    for l in range(len(data)):
      h = data[l].toGeohash(geohashlength)
      visited = set([h])
      neighbors = set([h])
      nonZeroNeighbors = [h] \
        if (h in hmap.countPerGeohash and hmap.countPerGeohash[h]>heatThreshold) \
        else []

      d=0
      while (len(nonZeroNeighbors)==0 and d<maxDistance):
        nneighbors = set([])
        for n in neighbors:
          nneighbors.union([h for h in geohash.neighbors(n) if h not in visited])
        neighbors = nneighbors
        for n in neighbors:
          if (n in hmap.countPerGeohash and hmap.countPerGeohash[n]>heatThreshold):
            nonZeroNeighbors.append(n)
        visited.union(neighbors)
        d+=1

      if len(nonZeroNeighbors)>0:
        if len(nonZeroNeighbors)>1:
          print h,nonZeroNeighbors
        lat,lon=0.,0.
        for n in nonZeroNeighbors:
          dlat,dlon = geohash.decode(n)
          lat += dlat
          lon += dlon
        ndata[l].location.lat= lat/len(nonZeroNeighbors)
        ndata[l].location.lon= lon/len(nonZeroNeighbors)

    return ndata

  def arrayDistanceInMeters(self,other):
    return TimedLocation.arrayDistanceInMeters(self.timedLocations,
        other.timedLocations)


class UniformlySampledRoute(Route):

  def __init__(self, timedLocations=[],sampling_period_in_sec=1.0):
    Route.__init__(self,timedLocations)
    self.timedLocations = \
      self.makeUniformlySampledRoute(sampling_period_in_sec).timedLocations
    self.sampling_period_in_sec = sampling_period_in_sec


class TimedLocation:

  def __init__(self,lat=0.0,lon=0.0,timestamp=0.0):
    self.location = Location(lat,lon)
    self.timestamp = timestamp

  def __str__(self):
    return self.toString()

  def toString(self):
    return "[%f: %s]"%(self.timestamp,self.location.toString())

  def toGeohash(self,geohashlength=7):
    return self.location.toGeohash(geohashlength)

  def intermediatePointTo(self,other,ratio):
    tl = TimedLocation()
    tl.location = self.location.intermediatePointTo(other.location,ratio)
    self.timestamp = self.timestamp+ratio*(other.timestamp-self.timestamp)
    return tl

  def distanceInMetersTo(self,other):
    return self.location.distanceInMetersTo(other.location)

  @staticmethod
  def makeTimedLocationFromCoordinatesAndTotalDuration(lonlats,totalDuration,
      prevTimestamp=0.0,latitudeFirst=False):

    if latitudeFirst:
      timedLocs = [TimedLocation(ss[0], ss[1], prevTimestamp) for ss in lonlats]
    else:
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

  @staticmethod
  def intermediatePoint(timedLoc1,timedLoc2,ratio):
    return timedLoc1.intermediatePointTo(timedLoc2,ratio)

  @staticmethod
  def distanceInMeters(location1,location2):
    return location1.distanceInMetersTo(location2)

  @staticmethod
  def arrayDistanceInMeters(a,b):
    if len(a)!=len(b):
      return []
    return [Location.distanceInMeters(b[i].location, a[i].location)
              for i in range(len(b))]
      

import geopy.distance
import random
import geomUtils
import geohash

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

  def toGeohash(self,geohashlength=7):
    return geohash.encode(self.lat,self.lon,geohashlength)

  def addNoise(self,noiseSigma=.005):
    self.lat += random.gauss(0.0,noiseSigma)
    self.lon += random.gauss(0.0,noiseSigma)

  def distanceInMetersTo(self,other):
    return geopy.distance.distance(
        self.toLatLonTuple(),
        other.toLatLonTuple()
      ).meters

  def intermediatePointTo(self,other,ratio):
    lat = self.lat+ratio*(other.lat-self.lat)
    lon = self.lon+ratio*(other.lon-self.lon)
    return Location(lat,lon)

  def __add__(self, other):
    """Control adding two Books together or a Book and a number"""
    return Location(self.lat+other.lat,self.lon+other.lon)

  def __radd__(self, other):
    """Control adding a Book and a number w/ the number first"""
    return other + self

  def __sub__(self, other):
    """Control adding two Books together or a Book and a number"""
    return Location(self.lat-other.lat,self.lon-other.lon)

  def __rsub__(self, other):
    """Control adding a Book and a number w/ the number first"""
    return other + self

  @staticmethod
  def distanceInMeters(location1,location2):
    return location1.distanceInMetersTo(location2)
    
  @staticmethod
  def intermediatePoint(location1,location2,ratio):
    return location1.intermediatePointTo(location2,ratio)
