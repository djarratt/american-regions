import igraph as ig
import louvain

YEAR = '1213'

G = ig.Graph.Read_Pickle('persistentGraph{0}.pickle'.format(YEAR))
