import datetime
import pytz as tz

import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.dates as mdates

import pyLeaflet

cdict = {'red':   ((0.0, 0.0, 0.0),
           (1.0, 1.0, 1.0)),

     'green': ((0.0, 0.0, 0.0),
           (1.0, 0.0, 0.0)),

     'blue':  ((0.0, 1.0, 1.0),
           (1.0, 0.0, 0.0))}
plt.register_cmap(cmap=colors.LinearSegmentedColormap('BlueRed', cdict))

def renderElement(route, save_to_file=None, ip='localhost', usePyLeaflet=False,
    **kwargs):
  # x,y,t = route.toLonLatTimeArrays()
  fig, ax1 = plt.subplots(figsize=(12, 9),nrows=1,ncols=1)
  
  # kwargs['marker'] = 'o' if not kwargs.has_key('marker') else kwargs['marker']
  # kwargs['s'] = [10]*len(x) if not kwargs.has_key('s') else kwargs['s']
  # # kwargs['cmap'] = \
  # #   plt.get_cmap('winter') if not kwargs.has_key('cmap') else kwargs['cmap']
  # kwargs['c'] = 'b' if not kwargs.has_key('c') else kwargs['c']
  # kwargs['alpha'] = .01 if not kwargs.has_key('alpha') else kwargs['alpha']
  # kwargs['linewidths'] = \
  #   0 if not kwargs.has_key('linewidths') else kwargs['linewidths']
    
  # ax1.scatter(x, y, **kwargs)
  route.render(ax1,**kwargs)

  ax1.axis('equal')
  ax1.set_xlabel('longitude')
  ax1.set_ylabel('latitude')
  
  ###############
  ###############
  if usePyLeaflet or (save_to_file is not None):
    # tile_layer = "http://{s}.tile.stamen.com/toner/{z}/{x}/{y}.jpg"
    tile_layer = "http://{s}.tile.stamen.com/terrain/{z}/{x}/{y}.jpg"
    html = pyLeaflet.plotWithMap(fig,tile_layer = tile_layer)
  # else:
    # plt.show()


def renderUser(user,save_to_file=None, ip='localhost', usePyLeaflet=False, 
    plot3d=False,**kwargs):
  utc_tz = tz.utc
  est_tz = tz.timezone('EST')
  x,y,times = user.toLonLatTimeArrays('filtered')
  x_actual,y_actual,times = user.toLonLatTimeArrays('actual')
  x_measured,y_measured,times = user.toLonLatTimeArrays('measured')
  start_time = (datetime.datetime(2016,01,01,8,0) 
                  - datetime.datetime(1970,1,1)).total_seconds()
  times = [datetime.datetime.fromtimestamp(t+start_time, est_tz) for t in times]

  kwargs['marker'] = 'o' if not kwargs.has_key('marker') else kwargs['marker']
  kwargs['alpha'] = .6 if not kwargs.has_key('alpha') else kwargs['alpha']
  kwargs['s'] = [10]*len(x) if not kwargs.has_key('s') else kwargs['s']
  kwargs['linewidths'] = 0 if not kwargs.has_key('linewidths') \
    else kwargs['linewidths']
  # kwargs['c'] = [abs(t.time().hour-13) for t in times]

  # print kwargs
  if plot3d:
    get_ipython().magic(u'matplotlib notebook')
    kwargs['cmap'] =  plt.get_cmap('BlueRed') if not kwargs.has_key('cmap') \
      else kwargs['cmap']
    fig = plt.figure(figsize=(12, 10))
    ax1 = plt.subplot2grid((6, 1), (0, 0),projection='3d',rowspan=6)
  #   ax1 = fig.add_subplot(611, projection='3d',rowspan=4)
    ax1.scatter(x, y, data['startepoch'], **kwargs)
    ax1.axis('equal')
    ax1.set_xlabel('longitude')
    ax1.set_ylabel('latitude')

  else:
    kwargs['cmap'] = plt.get_cmap('BlueRed') if not kwargs.has_key('cmap') \
      else kwargs['cmap']
    fig, (ax1,ax2,ax3,ax4) = plt.subplots(figsize=(16, 10),nrows=4,ncols=1)
    ax1.scatter(x, y, **kwargs)
    ax1.axis('equal')
    ax1.set_xlabel('longitude')
    ax1.set_ylabel('latitude')

    # if kwargs.has_key('alpha'):
    #   del kwargs['alpha']
    ax2.fmt_xdata = mdates.DateFormatter('%Y-%m-%d %H',est_tz)
    ax2.plot(times, y_actual,color='blue',linewidth=2)
    ax2.plot(times, y_measured,color='red',linewidth=2)
    ax2.plot(times, y,color='green',linewidth=2,linestyle='-.')
    ax2.set_xlabel('time')
    ax2.set_ylabel('lat')

    ax3.fmt_xdata = mdates.DateFormatter('%Y-%m-%d %H',est_tz)
    ax3.plot(times, x_actual,color='blue',linewidth=2)
    ax3.plot(times, x_measured,color='red',linewidth=2)
    ax3.plot(times, x,color='green',linewidth=2,linestyle='-.')
    ax3.set_xlabel('time')
    ax3.set_ylabel('lon')

    # ax4.fmt_xdata = mdates.DateFormatter('%Y-%m-%d %H',est_tz)
    # ax4.plot(times, user.errors_measured,color='red',linewidth=2)
    # ax4.plot(times, user.errors_filtered,color='green',linewidth=2,linestyle='-.')
    ax4.set_xlabel('time')
    ax4.set_ylabel('error')


  if usePyLeaflet or (save_to_file is not None):
    tile_layer = "http://{s}.tile.stamen.com/terrain/{z}/{x}/{y}.jpg"
    pyLeaflet.plotWithMap(fig,ip=ip,tile_layer = tile_layer,saveAs=save_to_file)
  else:
    plt.show()

  return