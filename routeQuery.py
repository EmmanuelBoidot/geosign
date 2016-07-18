import requests
from route import *

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

  def getUniformlySampledRoute(self,depLocation,arrLocation,sampling_period_in_sec):
    steps = self.getSteps(depLocation,arrLocation)
    route = UniformlySampledRoute(steps,sampling_period_in_sec)
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