import random
import geohash

from route import *


# A function to randomly select k items from stream[0..n-1].
def selectKItems(numPoints, numPointsToSample):
  # reservoir[] is the output array. Initialize it with
  # first k elements from stream[]
  reservoir = range(numPointsToSample)

  # Iterate from the (k+1)th element to nth element
  for i in range(numPointsToSample,numPoints):
    # Pick a random index from 0 to i.
    j = random.randrange(i+1);

    # If the randomly  picked index is smaller than k, then replace
    # the element present at the index with new element from stream
    if (j < numPointsToSample):
      reservoir[j] = i

  return sorted(reservoir)


def geohash_exactDistance(h1,h2):
    lat1,lon1 = geohash.decode(h1)
    lat2,lon2 = geohash.decode(h2)
    return Location(lat1, lon1).distanceInMetersTo(Location(lat2, lon2))


def geohashNeighbors(h,dist=2):
  if dist<=0:
    return {h:0}
  d = 1
  n = geohash.neighbors(h)
  s = dict(zip(n, [d for x in n]))
  while (d<dist):
    d+=1
    ss = set([])
    for hh  in s.keys():
      n = geohash.neighbors(hh)
      for k in n:
        if k not in s:
          ss.add(k)
    for k in ss:
      s[k] = d

  return s