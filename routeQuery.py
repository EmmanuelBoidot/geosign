import requests
from datetime import datetime

import googlemaps
import polyline

from route import *

# class RouteQuery:

  # def __init__(self,API='OSRM',**kwargs):
  #   if API=='Google':
  #     self = GoogleRouteQuery(**kwargs)
  #   else:
  #     self = OSRMRouteQuery(**kwargs)


class OSRMRouteQuery:

  def __init__(self,
      url="http://router.project-osrm.org/route/v1/",
      profile="driving",
      overview="false", steps="true", annotations="false", geometries="geojson",
      alternatives="false",continue_straight="default",**kwargs):
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

  def getRoute(self,depLocation,arrLocation,firstTimestamp=0.0):
    steps = self.getSteps(depLocation,arrLocation)
    timedLocations = OSRMRouteQuery.stepsToTimedLocationList(steps,firstTimestamp)
    route = Route(timedLocations)
    return route

  def getUniformlySampledRoute(self,depLocation,arrLocation,
      firstTimestamp=0.0,sampling_period_in_sec=1.0):
    route = self.getRoute(depLocation,arrLocation,firstTimestamp)
    return UniformlySampledRoute(route.timedLocations,sampling_period_in_sec)

  def getSteps(self,depLocation,arrLocation,travelMode='driving'):
    json = self.getJSON(depLocation,arrLocation,travelMode)
    steps = json['routes'][0]['legs'][0]['steps']
    return steps

  def getJSON(self,depLocation,arrLocation,travelMode='driving'):
    query = self.buildQuery(depLocation,arrLocation)
    try:
      json = requests.get(query).json()
    except ValueError:
      print query
      print "No JSON returned by server..."
      json = {'routes':[{'legs':[{'steps':[]}]}]}
    return json

  def buildQuery(self,depLocation,arrLocation):
    return "%s%s;%s%s"%(
              self.serverURL,
              depLocation.toLonLatString(),
              arrLocation.toLonLatString(),
              self.options
            )

  @staticmethod
  def stepsToTimedLocationList(steps=[],firstTimestamp=0.0,withPolyline=False):
    timedLocations = []
    
    if len(steps)==0:
      return timedLocations
      
    prevTimestamp = firstTimestamp
    if withPolyline:
      coordinates = polyline.decode(steps[0]['polyline']['points'])
      tl = TimedLocation(
              coordinates[0][0],
              coordinates[0][1],
              prevTimestamp
            )
    else:
      tl = TimedLocation(
              steps[0]['geometry']['coordinates'][0][1],
              steps[0]['geometry']['coordinates'][0][0],
              prevTimestamp
            )
    timedLocations.append(tl)
    
    for s in steps: # should be using 'geometry' instead
      if withPolyline:
        timedLocs = TimedLocation.makeTimedLocationFromCoordinatesAndTotalDuration(
                    polyline.decode(s['polyline']['points']),
                    s['duration'],
                    prevTimestamp,
                    withPolyline
                  )
      else:
        timedLocs = TimedLocation.makeTimedLocationFromCoordinatesAndTotalDuration(
                      s['geometry']['coordinates'],
                      s['duration'],
                      prevTimestamp,
                      withPolyline
                    )
      timedLocations.extend(timedLocs)
      prevTimestamp += s['duration']
      
    return timedLocations


class GoogleRouteQuery:
  def __init__(self):
    self.gmaps = googlemaps.Client(key=open('googleapi.key').readline())

  def getSteps(self,depLocation,arrLocation,travelMode='driving'):
    json = self.getJSON(depLocation,arrLocation,travelMode)
    steps = json[0]['legs'][0]['steps']
    return steps

  def getJSON(self,depLocation,arrLocation,travelMode='driving'):
    return self.gmaps.directions(
                          depLocation.toLatLonString(),
                          arrLocation.toLatLonString(),
                          mode=travelMode
                        )

  def getRoute(self,depLocation,arrLocation,firstTimestamp=0.0,travelMode='driving'):
    steps = self.getSteps(depLocation,arrLocation,travelMode)
    timedLocations = GoogleRouteQuery.stepsToTimedLocationList(steps,firstTimestamp)
    route = Route(timedLocations)
    return route

  def getUniformlySampledRoute(self,depLocation,arrLocation,
      firstTimestamp=0.0,sampling_period_in_sec=1.0):
    route = self.getRoute(depLocation,arrLocation,firstTimestamp)
    return UniformlySampledRoute(route.timedLocations,sampling_period_in_sec)

  @staticmethod
  def stepsToTimedLocationList(steps=[],firstTimestamp=0.0):
    timedLocations = []
    
    if len(steps)==0:
      return timedLocations
      
    prevTimestamp = firstTimestamp
    coordinates = polyline.decode(steps[0]['polyline']['points'])
    tl = TimedLocation(
            coordinates[0][0],
            coordinates[0][1],
            prevTimestamp
          )
    timedLocations.append(tl)
    
    for s in steps: # should be using 'geometry' instead
      timedLocs = TimedLocation.makeTimedLocationFromCoordinatesAndTotalDuration(
                  polyline.decode(s['polyline']['points']),
                  s['duration']['value'],
                  prevTimestamp,
                  latitudeFirst=True
                )
      timedLocations.extend(timedLocs)
      prevTimestamp += s['duration']['value']
      
    return timedLocations


