import requests
import geopy.distance

class RouteQuery:

  def __init__(self,
      url="http://router.project-osrm.org/route/v1/",
      profile="driving",
      overview="false", steps="true", annotations="false", geometries="geojson",
      alternatives="false",continue_straight="default"):
    self.serverURL = url+profile+"/"
    self.options = """?overview=%s&steps=%s&geometries=%s&annotations=%s&\
continue_straight=%s&alternatives=%s"""%(
                        overview,
                        steps,
                        geometries,
                        annotations,
                        continue_straight,
                        alternatives
                        )

  def getRoute(self,depLocation,arrLocation):
    steps = self.getSteps(depLocation,arrLocation)
    route = Route(steps)
    # for leg in json['routes'][0]['legs'][0:1]:
    #   print leg
    return route

  def getSteps(self,depLocation,arrLocation):
    json = self.getJSON(depLocation,arrLocation)
    steps = json['routes'][0]['legs'][0]['steps']
    return steps

  def getJSON(self,depLocation,arrLocation):
    query = self.buildQuery(depLocation,arrLocation)
    json = requests.get(query).json()
    return json

  def buildQuery(self,depLocation,arrLocation):
    return "%s%s;%s%s"%(
              self.serverURL,
              depLocation.toLonLatString(),
              arrLocation.toLonLatString(),
              self.options
            )


class Route:

  def __init__(self, steps=[]):
    self.timedLocations = []

    if len(steps)==0:
      return

    prevTimestamp = 0.0
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
                    s['distance'],
                    prevTimestamp
                  )
      self.timedLocations.extend(timedLocs)
      prevTimestamp += s['duration']

  def addPoint(self,lat,lon,timestamp):
    self.timedLocations.append(TimedLocation(lat,lon,timestamp))
    return

  def toLonLatArrays(self):
    X = [tl.location.lon for tl in self.timedLocations]
    Y = [tl.location.lat for tl in self.timedLocations]
    return X,Y

  def toString(self):
    return ",".join([tl.toString() for tl in self.timedLocations])


class TimedLocation:

  def __init__(self,lat,lon,timestamp):

    self.location = Location(lat,lon)
    self.timestamp = timestamp

  def toString(self):
    return "[%f: %s]"%(self.timestamp,self.location.toString())

  @staticmethod
  def makeTimedLocationFromCoordinatesAndTotalDuration(lonlats,totalDuration,
      totalDistance,prevTimestamp=0.0):

    timedLocs = [TimedLocation(ss[1], ss[0], prevTimestamp) for ss in lonlats]
    distances = [0.0]*len(lonlats)
    for i in range(1,len(lonlats)):
      distances[i] = Location.distanceInMeters(timedLocs[i-1].location,
                                                timedLocs[i].location)
      timedLocs[i].timestamp = totalDuration*distances[i]/totalDistance\
                                  +timedLocs[i-1].timestamp
    return timedLocs
      

class Location:

  def __init__(self,lat,lon):
    self.lat = lat
    self.lon = lon

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

  @staticmethod
  def distanceInMeters(location1,location2):
    return geopy.distance.distance(
      location1.toLatLonTuple(),
      location2.toLatLonTuple()
    ).meters