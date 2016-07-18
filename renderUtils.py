import matplotlib.pyplot as plt

import pyLeaflet

def renderRoute(route,**kwargs):
  x,y,t = route.toLonLatTimeArrays()
  fig, ax1 = plt.subplots(figsize=(15, 18),nrows=1,ncols=1)
  
  kwargs['marker'] = 'o' if not kwargs.has_key('marker') else kwargs['marker']
  kwargs['s'] = [10]*len(x) if not kwargs.has_key('s') else kwargs['s']
  # kwargs['cmap'] = \
  #     plt.get_cmap('winter') if not kwargs.has_key('cmap') else kwargs['cmap']
  kwargs['c'] = 'b' if not kwargs.has_key('c') else kwargs['c']
  kwargs['alpha'] = .01 if not kwargs.has_key('alpha') else kwargs['alpha']
  kwargs['linewidths'] = \
      0 if not kwargs.has_key('linewidths') else kwargs['linewidths']
      
  ax1.scatter(x, y, **kwargs)
  ax1.axis('equal')
  ax1.set_xlabel('longitude')
  ax1.set_ylabel('latitude')
  
  ###############
  ###############
  # tile_layer = "http://{s}.tile.stamen.com/toner/{z}/{x}/{y}.jpg"
  tile_layer = "http://{s}.tile.stamen.com/terrain/{z}/{x}/{y}.jpg"
  html = pyLeaflet.plotWithMap(fig,tile_layer = tile_layer)