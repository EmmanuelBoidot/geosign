import geohash

class Graph:

  def __init__(self,vertices=[],edges=set([])):
    self.parent = dict()
    self.rank = dict()
    for vertice in vertices:
      self.make_set(vertice)
    self.edges = edges


  def addEdge(self,e):
    self.edges.add(e)
    return

  def make_set(self,vertice):
    self.parent[vertice] = vertice
    self.rank[vertice] = 0

  def find(self,vertice):
    if self.parent[vertice] != vertice:
      self.parent[vertice] = self.find(self.parent[vertice])
    return self.parent[vertice]

  def union(self,vertice1, vertice2):
    root1 = self.find(vertice1)
    root2 = self.find(vertice2)
    if root1 != root2:
      if self.rank[root1] > self.rank[root2]:
        self.parent[root2] = root1
      else:
        self.parent[root1] = root2
        if self.rank[root1] == self.rank[root2]: 
          self.rank[root2] += 1


  def kruskal(self):
    import operator
    # for vertice in self.vertices:
    #   self.make_set(vertice)

    minimum_spanning_tree = set()
    edges = list(self.edges)
    edges.sort(key=operator.itemgetter(0,1))
  #   sorted(edges,key=itemgetter(0,1))

    for edge in edges:
      weight, weight2, vertice1, vertice2 = edge
      if self.find(vertice1) != self.find(vertice2):
        self.union(vertice1, vertice2)
        minimum_spanning_tree.add(edge)

    return Graph([],minimum_spanning_tree)


  def render(self,ax,usePyLeaflet=False,alpha=.7,save_to_file=None):
    for s in self.edges:
      lat1,lon1 = geohash.decode(s[2])
      lat2,lon2 = geohash.decode(s[3])
      ax.plot([lon1,lon2],[lat1,lat2],color='b',linewidth=3,alpha=alpha)