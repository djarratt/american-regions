import igraph as ig
import louvain
import csv
import random
import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from mpl_toolkits.basemap import Basemap


# graph import variables
MINIMUM_EDGE_WEIGHT = 0  # import only edges at this weight or greater

# community detection variables
RESOLUTION_LIST = [0.2, 0.3, 0.4, 0.5, 0.6]

# mapping variables
MINIMUM_COMMUNITY_SIZE = 3  # draw communities at this size or greater
MAP_NAME_PREFIX = "american-regions"
DRAW = "c"  # 'c' for crude, anything else for nice-quality map

# store node and edge information for preprocessing and filtering
nodes = []
edges = []
geo_coordinates = {}

# initialize the graph
G = ig.Graph(directed=True)

# import data
with open('government/national-gazetteer.tsv') as tsvfile:
    reader = csv.DictReader(tsvfile, delimiter='\t', quoting=csv.QUOTE_NONE)
    for row in reader:
        fips = row["GEOID"].strip()
        lat = row["INTPTLAT"].strip()
        lng = row["INTPTLONG"].strip()
        geo_coordinates[fips] = (lat, lng)

with open('generated-datasets/county-to-county1213.csv') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        fromCounty = row['fromCountyFIPSid']
        toCounty = row['toCountyFIPSid']
        # weight may also be set to the value of int(row['countTaxReturns']) or
        # int(row['sumAdjustedGrossIncome1000s'])
        weight = int(row['countTaxExemptions'])
        if weight >= MINIMUM_EDGE_WEIGHT:
            nodes.append(fromCounty)
            nodes.append(toCounty)
            edges.append((fromCounty, toCounty, weight))

# omit duplicate node IDs
nodes = set(nodes)

# fill the graph
for node in nodes:
    lat = geo_coordinates[node][0]
    lng = geo_coordinates[node][1]
    G.add_vertex(node, latitude=lat, longitude=lng)
for edge in edges:
    G.add_edge(edge[0], edge[1], weight=edge[2])

for res in RESOLUTION_LIST:
    # detect communities
    partition = louvain.find_partition(G, method='RBConfiguration',
                                       weight='weight',
                                       resolution_parameter=res)
    print("Found {0} communities at resolution {1}.".format(len(partition),
                                                            res))

    # draw the basemap
    plt.figure(figsize=(8, 4))
    m = Basemap(llcrnrlon=-119, llcrnrlat=22, urcrnrlon=-64, urcrnrlat=49,
                projection='lcc', lat_1=33, lat_2=45, lon_0=-95,
                resolution=DRAW)
    if DRAW == 'c':
        m.shadedrelief()
        m.drawrivers()
        DPI = 500
    else:
        DPI = 100
    m.drawcoastlines()
    m.drawstates()
    m.drawcountries()

    # draw points representing counties painted onto the basemap
    colors = iter(cm.rainbow(np.linspace(0, 1, len(partition))))
    drawnCommunities = 0
    for community in partition:
        color = next(colors)
        if len(community) >= MINIMUM_COMMUNITY_SIZE:
            drawnCommunities += 1
            for county in community:
                x, y = m(G.vs[county]["longitude"], G.vs[county]["latitude"])
                m.scatter(x, y, 3, marker='o', color=color)

    mapName = MAP_NAME_PREFIX + "-{0}-{1}-{2}-{3}-{4}-{5}.png".format(
                                                    datetime.datetime.today(),
                                                    MINIMUM_EDGE_WEIGHT,
                                                    MINIMUM_COMMUNITY_SIZE,
                                                    res, len(partition),
                                                    drawnCommunities)
    plt.savefig(mapName, dpi=DPI, bbox_inches='tight')
