#!python

# import json
# import requests

from routeQuery import *
import renderUtils as ru

rq = RouteQuery()
route = rq.getRoute(Location(40.536656, -74.489883),Location(40.433534, -74.222451))
# print route.toString()

ru.renderRoute(route)
