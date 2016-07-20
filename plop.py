# coding: utf-8

# In[24]:

import csv
import sys
import math
from datetime import datetime
import pytz as tz
from itertools import ifilter
import numpy as np
from StringIO import StringIO
import copy

from scipy.spatial import Delaunay
import matplotlib.pyplot as plt

import matplotlib.pyplot as plt
import matplotlib.path as mpath
import matplotlib.patches as mpatches
import matplotlib.colors as colors
from matplotlib.collections import PatchCollection
import matplotlib.dates as mdates
from mpl_toolkits.axes_grid1 import make_axes_locatable
from mpl_toolkits.mplot3d import Axes3D
get_ipython().magic(u'matplotlib inline')

import geohash

import mpld3
# mpld3.enable_notebook()

import pyLeaflet


# In[31]:

cdict = {'red':   ((0.0, 0.0, 0.0),
           (1.0, 1.0, 1.0)),

     'green': ((0.0, 0.0, 0.0),
           (1.0, 0.0, 0.0)),

     'blue':  ((0.0, 1.0, 1.0),
           (1.0, 0.0, 0.0))}
plt.register_cmap(cmap=colors.LinearSegmentedColormap('BlueRed', cdict))

def geohash_exactDistance(h1,h2):
  lat1,lon1 = geohash.decode(h1)
  lat2,lon2 = geohash.decode(h2)
  return distance_on_earth_in_meters(lat1, lon1, lat2, lon2)

# def geohash_approxDistance(h1,h2): # UNFINISHED !! need a 32x32 distance matrix
#   # cell size for hashlength 1 to 12
#   cell_width = [5000000,1250000,156000,39100,4890,1220,153,38.2,4.77,1.19,.149,.0372]
#   cell_height = [5000000,625000,156000,19500,489,610,153,19.1,4.77,.596,.149,.0186]
#   # distance as tuple (horizontal distance,vertical distance)
#   # the actual distance in meters should be multiplied by cell_width and cell_height values
#   geohash_distance_matrix = [(0,0),(1,0),(0,1),(1,1),(2,0),(3,0),(2,1),(3,1),(0,2),(1,2),(0,3),(1,3),(2,2),(3,2),(2,3),(3,3)]

#   mini = min(len(h1),len(h2))
#   h1 = h1[:mini]
#   h2 = h2[:mini]
#   d=0
#   while h1[d]==h2[d]:
#     d+=1

def diffEndingChar(h1,h2):
  d = min(len(h1),len(h2))-1
  c = 0
  while (d>=0 and h1[d]!=h2[d]):
    c+=1
    d-=1
  return c

#   return d

# geohash_exactDistance('gbsuxz','gbth8')

def fullprint(*args, **kwargs):
  from pprint import pprint
  import numpy
  opt = numpy.get_printoptions()
  numpy.set_printoptions(threshold='nan')
  pprint(*args, **kwargs)
  numpy.set_printoptions(**opt)


# In[58]:

def getUserRawTrajectory(fname, uid, delim=','):
  """
  Browses through a file in order to extract the lines corresponding to a specific
  user as specified by `uid`. Returns a dictionnary with keys `uid`,`trajectory`,
  `minTime` and `maxTime`. `userdata['trajectory']` is a list of trajectory elements
  with keys `latLng`,startepoch`,`endepoch`.

  !!! Assumes the file is ordered by user, by startepoch. Needs the file to have
  `lat`,`lon`,`startepoch`,`endepoch`.

  Args:
  * `fname` (str);
  * `uid` (str):

  Returns:
  * `userdata` (dict):
  * `userdatatxt` (str):

  """
  userdata = {'uid':uid, 'trajectory':[], 'minTime':0, 'maxTime':0}
  userdatatxt = ""

  reader = csv.reader(open(fname,"rb"),delimiter=delim)
  header = next(reader,None)

  userdatatxt = ",".join(header)
  # get fieldname to column mapping
  fieldMap = {}
  for idx, h in enumerate(header):
    fieldMap[h] = idx
  # find the first line where the user appears
  for line in reader:
    if line[0]==uid:
      userdata['minTime'] = int(line[fieldMap['startepoch']])
      userdata['trajectory'].append({'latLng':{'lat':float(line[fieldMap['lat']]),'lon':float(line[fieldMap['lon']])},'startepoch':int(line[fieldMap['startepoch']]),'endepoch':int(line[fieldMap['endepoch']])})
      userdatatxt = userdatatxt+'\n'+",".join(line)
      break

  # if the min time is still 0, then the user was not seen in the file
  if userdata['minTime']==0:
    print "getUserRawTrajectory - The user '%s' is not present in this file."
    return userdata

  # from this line, read the file until the uid changes
  for line in reader:
    if line[0]!=uid:
      break
    userdata['trajectory'].append({'latLng':{'lat':float(line[fieldMap['lat']]),'lon':float(line[fieldMap['lon']])},'startepoch':int(line[fieldMap['startepoch']]),'endepoch':int(line[fieldMap['endepoch']])})
    userdatatxt = userdatatxt+'\n'+",".join(line)

  userdata['maxTime'] = userdata['trajectory'][-1]['endepoch']

  return userdata,userdatatxt

def render_user_from_file(fname,uid,delim=',',save_to_file=None, ip='localhost', usePyLeaflet=False, **kwargs):
  data = getUserTrajectoryAsNumpyArray(fname,uid,delim=delim)
  render_user(data,save_to_file=save_to_file, ip=ip, usePyLeaflet=usePyLeaflet, **kwargs)
  return


def getUserTrajectoryAsNumpyArray(fname,uid,delim=","):
  plop,usertxt = getUserRawTrajectory(fname,uid,delim=delim)
  data = np.genfromtxt(StringIO(usertxt),names=True,skip_header=0,delimiter=",",dtype="S16,i,i,f,f,i")
  return data

# def renderGeohashHeatmap(hmap, ip='localhost',save_to_file=None,alpha=.7,usePyLeaflet=False,minValueThreshold=-float('Inf')):
#   if not usePyLeaflet:
#     alpha=1.0

#   fig, ax1 = plt.subplots(figsize=(12, 10),nrows=1,ncols=1)

#   minlat = 180.
#   maxlat = -180.
#   minlon= 180.
#   maxlon = -180.
#   patches = []
#   values = []
#   colorvalues = []
#   for d in hmap.keys():
#     try:
#       if (hmap[d]>minValueThreshold):
#         bbox = geohash.bbox(d)
#         minlon = minlon if (minlon < bbox['w']) else bbox['w']
#         minlat = minlat if (minlat < bbox['n']) else bbox['n']
#         maxlon = maxlon if (maxlon > bbox['e']) else bbox['e']
#         maxlat = maxlat if (maxlat > bbox['s']) else bbox['s']
#         rect = mpatches.Rectangle([ bbox['w'],
#                       bbox['s']],
#                       bbox['e'] - bbox['w'],
#                       bbox['n'] - bbox['s'],
#                       ec='none', lw=.1, fc='red', alpha=alpha)
#         patches.append(rect)
#         values.append(hmap[d] if hmap[d]<3 else hmap[d]+10)
#         colorvalues.append(hmap[d] if hmap[d]<3 else hmap[d]+10)
#     except:
#       print "'"+d +"' is not a valid geohash."

#   print max(values)

#   p = PatchCollection(patches,cmap=plt.get_cmap('BlueRed'),alpha=alpha)
# #   if usePyLeaflet:
#   if (len(values)<100):
#     p.set_edgecolors(np.array(['black' for x in values]))
#   else:
#     p.set_edgecolors(np.array(['#333333' if x<=2 else ('#666666' if x<=10 else 'black') for x in values]))
# #   else:
# #     p.set_edgecolors(np.array(['white' for x in values]))
#   p.set_array(np.array(colorvalues))
#   p.set_norm(colors.LogNorm(vmin=1, vmax=max(values)+1))
#   ax1.add_collection(p)
#   ax1.set_xlim(minlon, maxlon)
#   ax1.set_ylim(minlat, maxlat)
#   divider = make_axes_locatable(ax1)
#   cbar = plt.colorbar(p)
#   cbar.set_clim(vmin=max(1,min(values)),vmax=max(values)+1)
#   cbar.update_normal(p)

#   if usePyLeaflet:
#     tile_layer = "http://{s}.tile.stamen.com/terrain/{z}/{x}/{y}.jpg"
#     pyLeaflet.plotWithMap(fig,ip=ip,tile_layer = tile_layer,saveAs=save_to_file)
#   else:
#     plt.show()
#   return


# this is probably a rather slow process. Improving the method
# using the fact that neighbors hash are deterministic
# (the grid is fixed) would be a good idea to boost performance
# def geohashNeighbors(h,dist=2):
#   if dist<=0:
#     return {h:0}
#   d = 1
#   n = geohash.neighbors(h)
#   s = dict(zip(n, [d for x in n]))
#   while (d<dist):
#     d+=1
#     ss = set([])
#     for hh  in s.keys():
#       n = geohash.neighbors(hh)
#       for k in n:
#         if k not in s:
#           ss.add(k)
#     for k in ss:
#       s[k] = d

#   return s

def bilateral_filter(hmap,maxdist=2,sigma=None):
  if sigma is None:
    sigma=maxdist*5.0/9

  mtotal = 1.0
  weights = np.zeros(maxdist+1)
  weights[0] = 1.0
  for d in range(1,maxdist+1):
    weights[d] = math.exp(-d*d/(2*sigma*sigma))
    mtotal += 8*d*weights[d]

#   print mtotal,weights

  kk = hmap.keys()
  nhmap = dict(zip(kk, [0.0 for x in kk]))
  maxi = hmap['maxvalue']
  for k in kk:
    if k in ['minlon','minlat','maxlon','maxlat','maxvalue','geohashlength']:
      continue

    nhmap[k] += hmap[k]*1.0/maxi/mtotal
    nn = geohashNeighbors(k,dist=maxdist)
    for n in nn.keys():
      try:
        nhmap[k] += hmap[n]*1.0/weights[nn[n]]/mtotal/maxi
      except:
        # do nothing
        nhmap[k] += 0.0

#   nhmap['maxvalue'] = max(nhmap.values())
  for k in ['minlon','minlat','maxlon','maxlat','maxvalue','geohashlength']:
    nhmap[k] = hmap[k]

  return nhmap

def bilateral_sharpen(hmap,maxdist=2):
  nhmap = bilateral_filter(hmap,maxdist=2*maxdist)
  mini = 0
  maxi = hmap['maxvalue']
#   maxi2 = nhmap['maxvalue']

#   print maxi,maxi2

  for k in nhmap.keys():
    if k in ['minlon','minlat','maxlon','maxlat','maxvalue','geohashlength']:
      continue

    try:
      nhmap[k] = (1.5*hmap[k]/maxi-0.5*nhmap[k])*maxi
    except:
      nhmap[k] = 0#-0.5*nhmap[k]
#     mini = min(mini,nhmap[k])

#   for k in nhmap.keys():
#     nhmap[k] -= mini

  nhmap['maxvalue'] = 1

  return nhmap

def computeUserSignature(data,geohashlength=8,maxInterpolationTimeInterval=300,ip='localhost',maxInterpolationDistance=1000):
  # became Route.toHeatmap()
  return

def filterFromSignature(data,hmap,maxDistance=5,heatThreshold=.01):
  ndata = copy.deepcopy(data)
  geohashlength = hmap['geohashlength']
  for l in range(len(data)):
    h = geohash.encode(data[l]['lat'],data[l]['lon'],geohashlength)
    visited = set([h])
    neighbors = set([h])
    nonZeroNeighbors = [h] if (h in hmap and hmap[h]>heatThreshold) else []
    d=0
    while (len(nonZeroNeighbors)==0 and d<maxDistance):
      nneighbors = set([])
      for n in neighbors:
        nneighbors.union([h for h in geohash.neighbors(n) if h not in visited])
      neighbors = nneighbors
      for n in neighbors:
        if (n in hmap and hmap[n]>heatThreshold):
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
      ndata[l]= Location(lat/len(nonZeroNeighbors),
                            lon/len(nonZeroNeighbors),
                            data[l].timestamp)

  return ndata


# In[61]:

fname = "nfl_sample.txt"
uid_studied = "03aafa316cecaff0"
# uid_studied = "0c9e87b0713b84c7"
# uid_studied = "235f0a49b3ec7094"
# uid_studied = "d1ca8d309e1a6ed2"
data = getUserTrajectoryAsNumpyArray(fname,uid_studied,delim="\t")
# data = np.concatenate((data[1050:1100],data[1620:1700]),axis=0)

render_user(data,ip="md-bdadev-149.verizon.com",plot3d=False,usePyLeaflet=False)
hmap0 = computeUserSignature(data,ip="md-bdadev-149.verizon.com",geohashlength=7,maxInterpolationDistance=1)
renderGeohashHeatmap(hmap0,ip="md-bdadev-149.verizon.com",usePyLeaflet=False)


# In[62]:

hmap = computeUserSignature(data,ip="md-bdadev-149.verizon.com",maxInterpolationTimeInterval=1000,geohashlength=7,maxInterpolationDistance=1000)
nhmap = bilateral_filter(hmap,maxdist=5)
# nhmap = bilateral_filter(nhmap,maxdist=5)
# nhmap = bilateral_filter(nhmap,maxdist=5)
shmap = bilateral_sharpen(hmap,maxdist=5)


# In[63]:

renderGeohashHeatmap(hmap,ip="md-bdadev-149.verizon.com",usePyLeaflet=False)
renderGeohashHeatmap(nhmap,ip="md-bdadev-149.verizon.com",usePyLeaflet=False)
renderGeohashHeatmap(shmap,ip="md-bdadev-149.verizon.com",usePyLeaflet=False,alpha=.8,minValueThreshold=0.0)
renderGeohashHeatmap(shmap,ip="md-bdadev-149.verizon.com",usePyLeaflet=False,alpha=.8,minValueThreshold=10.0)
# renderGeohashHeatmap(shmap,ip="md-bdadev-149.verizon.com",usePyLeaflet=True,alpha=.7,\
#            minValueThreshold=1.0,save_to_file='denoised.html')
# renderGeohashHeatmap(hmap,ip="md-bdadev-149.verizon.com",usePyLeaflet=True,alpha=.7,\
#            minValueThreshold=0.0,save_to_file='noisy.html')
# print shmap


# In[ ]:

# visited = set([])
# print [h in shmap for h in geohash.neighbors('dr7b423') if h not in visited]
print max(shmap.values())
ndata = filterFromSignature(data,shmap,maxDistance=5,heatThreshold=10)


# In[7]:

def compareTimeseries(data,ndata,usePyLeaflet=False,st=0,et=None,**kwargs):
  if et is None or et>min(len(data),len(ndata)):
    et=min(len(data),len(ndata))

  utc_tz = tz.utc
  est_tz = tz.timezone('EST')
  x, y =  data[st:et]['lon'],data[st:et]['lat']
  nx, ny =  ndata[st:et]['lon'],ndata[st:et]['lat']
  times = [datetime.fromtimestamp(b, est_tz) for b in data[st:et]['startepoch']]
  try:
    error = data[st:et]['error']
  except:
    error = None

  #   data = np.genfromtxt(fname,names=True,skip_header=0,delimiter=delim,dtype="S16,i,i,f,f,i")
  #   valid_user = (data['deviceid'][:]==uid)
  #   x, y =  data['lon'][valid_user],data['lat'][valid_user]
  #   times = [datetime.fromtimestamp(b, utc_tz) for b in data['startepoch'][valid_user]]

  #   try:
  #     error = data['error'][valid_user]
  #   except:
  #     error = None

  #   fig, (ax1,ax2,ax3) = plt.subplots(figsize=(16, 10),nrows=3,ncols=1)

  # this plots the lines of the csv as markers, colored as a function
  # of the column `info1`, with a linear colormap blue->green
  kwargs = {}
  kwargs['marker'] = 'o' if not kwargs.has_key('marker') else kwargs['marker']
  kwargs['s'] = [10]*len(x) if not kwargs.has_key('s') else kwargs['s']
  #kwargs['c'] = data['info1'] if not kwargs.has_key('c') else kwargs['c']
  kwargs['linewidths'] =     0 if not kwargs.has_key('linewidths') else kwargs['linewidths']

  if error is not None:
    kwargs['c'] = [abs(t.time().hour-13) for t in times]#error

  kwargs['cmap'] =     plt.get_cmap('BlueRed') if not kwargs.has_key('cmap') else kwargs['cmap']
  fig, (ax1,ax2,ax3,ax4,ax5) = plt.subplots(figsize=(16, 10),nrows=5,ncols=1)
  ax1.scatter(nx, ny, **kwargs)
  ax1.axis('equal')
  ax1.set_xlabel('corr. longitude')
  ax1.set_ylabel('corr. latitude')

  ax2.scatter(x, y, **kwargs)
  ax2.axis('equal')
  ax2.set_xlabel('longitude')
  ax2.set_ylabel('latitude')

  ax3.fmt_xdata = mdates.DateFormatter('%Y-%m-%d %H',est_tz)
  ax3.plot(times, ny,color='red',linewidth=2)
  ax3.plot(times, y,color='blue',linewidth=1)
  ax3.set_xlabel('time')
  ax3.set_ylabel('lat')

  ax4.fmt_xdata = mdates.DateFormatter('%Y-%m-%d %H',est_tz)
  ax4.plot(times, nx,color='red',linewidth=2)
  ax4.plot(times, x,color='blue',linewidth=1)
  ax4.set_xlabel('time')
  ax4.set_ylabel('lon')

  distanceAfterFiltering = [distance_on_earth_in_meters(y[l],x[l],ny[l],nx[l]) for l in range(len(x))]
  ax5.fmt_xdata = mdates.DateFormatter('%Y-%m-%d %H',est_tz)
  ax5.plot(times, distanceAfterFiltering,color='red',linewidth=2)
  ax5.plot(times, error,color='blue',linewidth=1)
  ax5.set_xlabel('time')
  ax5.set_ylabel('error')

  if usePyLeaflet:
    tile_layer = "http://{s}.tile.stamen.com/terrain/{z}/{x}/{y}.jpg"
    pyLeaflet.plotWithMap(fig,ip="md-bdadev-149.verizon.com",tile_layer = tile_layer,saveAs=None)
  else:
    plt.show()

  get_ipython().magic(u'matplotlib inline')
  return


# In[ ]:

compareTimeseries(data,ndata)


# In[ ]:

len(hmap.keys())


# In[ ]:

# gh = ['dr7b2yt', 'dr7b2w3', 'dr7b2my', 'dr7b2ws', 'dr7b2tb', 'dr7b2my', 'dr7b2qm', 'dr7b2wu', 'dr7b2x3', 'dr7b2qn', 'dr7b2w8', 'dr7b2wc', 'dr7b2zv', 'dr7b2qt', 'dr7b2qs', 'dr78rgs', 'dr78ryf', 'dr7b2x5', 'dr7b3jj', 'dr7b2qp', 'dr7b3jb', 'dr78rwy', 'dr7b2x2', 'dr78rwy', 'dr7b2rd', 'dr7b2x8', 'dr7b2rg', 'dr7b2rg', 'dr7b2rg', 'dr7b82n', 'dr7b827', 'dr7b2rt', 'dr7b82n', 'dr7b2rw', 'dr7b82m', 'dr7b82j']
# hmap = dict(zip(gh, [100 for x in gh]))
# renderGeohashHeatmap(hmap,ip='md-bdadev-149.verizon.com',usePyLeaflet=True)


# In[ ]:

# from skimage import data, img_as_float
# from skimage.restoration import denoise_tv_chambolle, denoise_bilateral


# astro = img_as_float(data.astronaut())


# In[ ]:

for d in range(1,3+1):
  print d


# In[ ]:

max(hmap.values())


# In[ ]:

maxdist=3
for d in range(maxdist+1):
  print math.pow(3,maxdist-d)


# In[ ]:




# In[ ]:

utc_tz = tz.utc
est_tz = tz.timezone('EST')
print datetime.fromtimestamp(1449440266, utc_tz)
print datetime.fromtimestamp(1449440266, est_tz).time().hour


# In[ ]:

mdates.DateFormatter('%Y-%m-%d %H').set_tzinfo(est_tz)


# In[ ]:

plop = set(['a'])
plop.union(['a','b'])


# In[ ]:

# validKeys = [h for h in shmap.keys() if shmap[h]>1.0 and h not in ['minlon','minlat','maxlon','maxlat','maxvalue','geohashlength']]
# points = np.array([geohash.decode(h) for h in validKeys])
# from scipy.spatial import Delaunay
# tri = Delaunay(points)
# import matplotlib.pyplot as plt
# plt.triplot(points[:,0], points[:,1], tri.simplices.copy())
# plt.plot(points[:,0], points[:,1], 'o')
# plt.show()
# indices = tri.vertex_neighbor_vertices
# print indices
# print tri.simplices
# # len(hmap.keys())


# In[51]:

def hmapToGraph(hmap,heatThreshold=-float('Inf')):
  validKeys = [h for h in hmap.keys() if hmap[h]>heatThreshold and h not in ['minlon','minlat','maxlon','maxlat','maxvalue','geohashlength']]
  points = np.array([geohash.decode(h) for h in validKeys])
  tri = Delaunay(points)
#   neighbors = dict(zip(validKeys, [[] for x in validKeys]))
  # print neighbors
  graph = {'vertices':validKeys,
      'edges':set([])}
  for t in tri.simplices:
    for i in range(3):
      graph['edges'].add((geohash_exactDistance(validKeys[t[i]],validKeys[t[(i+1)%3]]),hmap[validKeys[t[i]]]+hmap[validKeys[t[(i+1)%3]]],validKeys[t[i]],validKeys[t[(i+1)%3]]))
  return graph


# In[ ]:




# In[39]:

parent = dict()
rank = dict()

def make_set(vertice):
  parent[vertice] = vertice
  rank[vertice] = 0

def find(vertice):
  if parent[vertice] != vertice:
    parent[vertice] = find(parent[vertice])
  return parent[vertice]

def union(vertice1, vertice2):
  root1 = find(vertice1)
  root2 = find(vertice2)
  if root1 != root2:
    if rank[root1] > rank[root2]:
      parent[root2] = root1
    else:
      parent[root1] = root2
      if rank[root1] == rank[root2]: rank[root2] += 1

def kruskal(graph):
  import operator
  for vertice in graph['vertices']:
    make_set(vertice)

  minimum_spanning_tree = set()
  edges = list(graph['edges'])
  edges.sort(key=operator.itemgetter(0,1))
#   sorted(edges,key=itemgetter(0,1))
  for edge in edges:
    weight, weight2, vertice1, vertice2 = edge
    if find(vertice1) != find(vertice2):
      union(vertice1, vertice2)
      minimum_spanning_tree.add(edge)
  return minimum_spanning_tree

def plotGeoHashTree(mset,usePyLeaflet=False,save_to_file=None):
  fig, ax = plt.subplots(figsize=(16, 10),nrows=1,ncols=1)
  for s in mset:
    lat1,lon1 = geohash.decode(s[2])
    lat2,lon2 = geohash.decode(s[3])
    ax.plot([lon1,lon2],[lat1,lat2],color='b',linewidth=3,alpha=.7)
  if usePyLeaflet or (save_to_file is not None):
    tile_layer = "http://{s}.tile.stamen.com/terrain/{z}/{x}/{y}.jpg"
    pyLeaflet.plotWithMap(fig,ip="md-bdadev-149.verizon.com",tile_layer = tile_layer,saveAs=save_to_file)
  else:
    plt.show()


# In[64]:

graph = hmapToGraph(shmap,heatThreshold=.0)
# print graph


# In[65]:

usign = kruskal(graph)


# In[ ]:

# plotGeoHashTree(usign)
plotGeoHashTree(usign,usePyLeaflet=True,save_to_file='signature.html')


# In[ ]:




# In[ ]: