import os
import json

import requests
from datetime import datetime

import googlemaps
import polyline

from route import *

class RouteQuery:

  def getSteps(self,depLocation,arrLocation,travelMode='driving'):
    json = self.getJSON(depLocation,arrLocation,travelMode)
    steps = json['routes'][0]['legs'][0]['steps']
    return steps

  def getJSON(self,depLocation,arrLocation,travelMode='driving'):
    fname = depLocation.toGeohash(9)+'_'+arrLocation.toGeohash(9)
    mpath = os.path.join(os.path.dirname(os.path.realpath(__file__)),'cache','google',fname)
    if os.path.exists(mpath):
      print("Route exists in cache. Loading from cache...")
      jsons = json.loads(open(mpath).read())
    else:
      query = self.buildQuery(depLocation,arrLocation)
      try:
        jsons = requests.get(query).json()
        json.dump(jsons,open(mpath,'w'))
      except ValueError:
        print query
        print "No JSON returned by server..."
        jsons = {'routes':[{'legs':[{'steps':[]}]}]}

      json.dump(jsons,open(mpath,'w'))

    return jsons


class OSRMRouteQuery(RouteQuery):

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

  # def getSteps(self,depLocation,arrLocation):
  #   json = self.getJSON(depLocation,arrLocation)
  #   steps = json['routes'][0]['legs'][0]['steps']
  #   return steps

  # def getJSON(self,depLocation,arrLocation):
  #   fname = depLocation.toGeohash(9)+'_'+arrLocation.toGeohash(9)
  #   mpath = os.path.join(os.path.dirname(os.path.realpath(__file__)),'cache','osrm',fname)
  #   if os.path.exists(mpath):
  #     print("Route exists in cache. Loading from cache...")
  #     jsons = json.loads(open(mpath).read())
  #   else:
  #     query = self.buildQuery(depLocation,arrLocation)
  #     try:
  #       jsons = requests.get(query).json()
  #       json.dump(jsons,open(mpath,'w'))
  #     except ValueError:
  #       print query
  #       print "No JSON returned by server..."
  #       jsons = {'routes':[{'legs':[{'steps':[]}]}]}

  #   return jsons

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


class GoogleRouteQuery(RouteQuery):
  def __init__(self,serverURL="https://maps.googleapis.com/maps/api/directions/json"):
    self.key = open('googleapi.key').readline()
    self.gmaps = googlemaps.Client(key=self.key)
    self.serverURL = serverURL
    self.options = ""

  def buildQuery(self,depLocation,arrLocation):
    return "%s?origin=%s&destination=%s%s"%(
              self.serverURL,
              depLocation.toLatLonString(),
              arrLocation.toLatLonString(),
              self.options
            )

  # def getSteps(self,depLocation,arrLocation,travelMode='driving'):
  #   json = self.getJSON(depLocation,arrLocation,travelMode)
  #   steps = json[0]['legs'][0]['steps']
  #   return steps

  # def getJSON(self,depLocation,arrLocation,travelMode='driving'):
  #   fname = depLocation.toGeohash(9)+'_'+arrLocation.toGeohash(9)
  #   mpath = os.path.join(os.path.dirname(os.path.realpath(__file__)),'cache','google',fname)
  #   if os.path.exists(mpath):
  #     print("Route exists in cache. Loading from cache...")
  #     jsons = json.loads(open(mpath).read())
  #   else:
  #     jsons =  self.gmaps.directions(
  #                         depLocation.toLatLonString(),
  #                         arrLocation.toLatLonString(),
  #                         mode=travelMode
  #                       )
  #     json.dump(jsons,open(mpath,'w'))

  #   return jsons

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


