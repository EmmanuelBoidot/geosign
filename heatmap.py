import numpy as np
from scipy.spatial import Delaunay
import math

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as colors
from matplotlib.collections import PatchCollection
from mpl_toolkits.axes_grid1 import make_axes_locatable

import geohash

import geomUtils as gu
from route import *

class Heatmap:

  def __init__(self,countPerGeohash):
    self.countPerGeohash = countPerGeohash
    self.bbox = {'n':countPerGeohash['maxlat'],
                 'e':countPerGeohash['maxlon'],
                 's':countPerGeohash['minlat'],
                 'w':countPerGeohash['minlon']
                }
    self.maxvalue = max(countPerGeohash['maxvalue'],1.0)
    self.geohashlength = countPerGeohash['geohashlength']

    self.removeGeohashes(['minlon','minlat','maxlon','maxlat','maxvalue',
        'geohashlength'])

  def normalize(self):
    for k in self.countPerGeohash.keys():
      self.countPerGeohash[k] *= 1.0/self.maxvalue
    self.maxvalue = 1.0


  def render(self,ax,alpha=.7,usePyLeaflet=False,
      minValueThreshold=-float('Inf'),logScale=True):
    if not usePyLeaflet:
      alpha=1.0

    patches = []
    values = []
    colorvalues = []
    for d in self.countPerGeohash.keys():
      try:
        if (self.countPerGeohash[d]>minValueThreshold):
          bbox = geohash.bbox(d)
          rect = mpatches.Rectangle([ bbox['w'],
                        bbox['s']],
                        bbox['e'] - bbox['w'],
                        bbox['n'] - bbox['s'],
                        ec='none', lw=.1, fc='red', alpha=alpha)
          patches.append(rect)
          # values.append(self.countPerGeohash[d] \
          #   if self.countPerGeohash[d]<3 else self.countPerGeohash[d]+10)
          # colorvalues.append(self.countPerGeohash[d] \
          #   if self.countPerGeohash[d]<3 else self.countPerGeohash[d]+10)
          values.append(self.countPerGeohash[d])
          colorvalues.append(self.countPerGeohash[d])
      except KeyError:
        print("'"+d +"' is not a valid geohash.")

    try:
      maxval = max(values)
      minval = min(values)
    except ValueError:
      print('heatmap appears to be empty...')
      maxval = 1
      minval = 0

    p = PatchCollection(patches,cmap=plt.get_cmap('BlueRed'),alpha=alpha)
  #   if usePyLeaflet:
    if (len(values)<100):
      p.set_edgecolors(np.array(['black' for x in values]))
    else:
      p.set_edgecolors(np.array(['#333333' if x<=2 \
        else ('#666666' if x<=10 else 'black') for x in values]))
  #   else:
  #     p.set_edgecolors(np.array(['white' for x in values]))
    p.set_array(np.array(colorvalues))
    if logScale:
      p.set_norm(colors.LogNorm(vmin=.01, vmax=maxval+1))
    else:
      p.set_norm(colors.Normalize(vmin=0, vmax=maxval))
    ax.add_collection(p)
    ax.set_xlim(self.bbox['w'], self.bbox['e'])
    ax.set_ylim(self.bbox['s'], self.bbox['n'])
    divider = make_axes_locatable(ax)
    cbar = plt.colorbar(p)
    cbar.set_clim(vmin=max(0,minval),vmax=maxval)
    cbar.update_normal(p)
    return


  def removeGeohashes(self,entries):
    for key in entries:
      if key in self.countPerGeohash:
        del self.countPerGeohash[key]


  def toGraph(self,heatThreshold=-float('Inf')):
    validKeys = [h for h in self.countPerGeohash.keys() \
      if self.countPerGeohash[h]>heatThreshold]
    points = np.array([geohash.decode(h) for h in validKeys])
    tri = Delaunay(points)
  #   neighbors = dict(zip(validKeys, [[] for x in validKeys]))
    # print neighbors
    graph = {'vertices':validKeys, 'edges':set([])}
    for t in tri.simplices:
      for i in range(3):
        graph['edges'].add(
          (gu.geohash_exactDistance(validKeys[t[i]],validKeys[t[(i+1)%3]]),
            self.countPerGeohash[validKeys[t[i]]]+self.countPerGeohash[validKeys[t[(i+1)%3]]],
            validKeys[t[i]],validKeys[t[(i+1)%3]]))
    return graph

  def computeBilateralFilteredCountsPerGeohash(self,maxdist=2,sigma=None):
    if sigma is None:
      sigma=maxdist*5.0/9

    mtotal = 1.0
    weights = np.zeros(maxdist+1)
    weights[0] = 1.0
    for d in range(1,maxdist+1):
      weights[d] = math.exp(-d*d/(2*sigma*sigma))
      mtotal += 8*d*weights[d]

  #   print mtotal,weights

    kk = self.countPerGeohash.keys()
    nhmap = dict(zip(kk, [0.0 for x in kk]))
    maxi = self.maxvalue
    for k in kk:
      nhmap[k] += self.countPerGeohash[k]*1.0/maxi/mtotal
      nn = gu.geohashNeighbors(k,dist=maxdist)
      for n in nn.keys():
        try:
          nhmap[k] += self.countPerGeohash[n]*1.0/weights[nn[n]]/mtotal/maxi
        except:
          # do nothing
          nhmap[k] += 0.0

    return nhmap

  def bilateral_sharpen(self,maxdist=2):
    nhmap = self.computeBilateralFilteredCountsPerGeohash(maxdist=2*maxdist)
    mini = 0
    maxi = self.maxvalue
  #   maxi2 = nhmap['maxvalue']

  #   print maxi,maxi2

    for k in nhmap.keys():
      try:
        nhmap[k] = (1.5*hmap[k]/maxi-0.5*nhmap[k])*maxi
      except:
        nhmap[k] = 0#-0.5*nhmap[k]
  #     mini = min(mini,nhmap[k])

  #   for k in nhmap.keys():
  #     nhmap[k] -= mini

    self.maxvalue = 1
    self.countPerGeohash = nhmap
    return 