import igraph as ig
import louvain as louvain
import csv as csv
import random
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from mpl_toolkits.basemap import Basemap

def plot_graph(G, file, partition):
  ig.plot(G, target=file, vertex_color=partition.membership,
        mark_groups=zip(map(list, partition.community.values()), 
                        partition.community.keys()),
        vertex_frame_width=0,
        palette=ig.RainbowPalette(len(partition.community)))

nodes = []
edges = []
weights = []
geo = {}
G = ig.Graph(directed=True)

with open('government/national-gazetteer.tsv') as tsvfile:
    reader = csv.DictReader(tsvfile,delimiter='\t', quoting=csv.QUOTE_NONE)
    for row in reader:
        fips = row["GEOID"].strip()
        lat = row["INTPTLAT"].strip()
        lng = row["INTPTLONG"].strip()
        geo[fips] = (lat, lng)

with open('generated-datasets/county-to-county1213.csv') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        fromCounty = row['fromCountyFIPSid']
        toCounty = row['toCountyFIPSid']
        weight = int(row['countTaxExemptions'])
        if weight > 0:
            nodes.append(fromCounty)
            nodes.append(toCounty)
            edges.append((fromCounty, toCounty, weight))
            weights.append(weight)
        
nodes = set(nodes)
for n in nodes:
    lat = geo[n][0]
    lng = geo[n][1]
    G.add_vertex(n, latitude=lat, longitude=lng)
for e in edges:
    G.add_edge(e[0], e[1], weight=e[2])


#ig.summary(G)
#print(G)

opt = louvain.Optimiser();
partition_modularity = opt.find_partition(G, louvain.ModularityVertexPartition);  #ModularityVertexPartition
#for c in p_mod.community:
#    print(p_mod.community[c])

communityCount = len(partition_modularity.community)
for partition in partition_modularity.community:
    community = partition_modularity.community[partition]
    for county in community:
        print("Partition {0} County {1}".format(partition, G.vs[county]["name"]))

#p_mod_rb = louvain.RBConfigurationVertexPartition(G, resolution=1, membership=p_mod.membership);
#G['layout'] = G.layout_auto();
#plot_graph(G, 'counties_comm_mod.pdf', partition_modularity);

m = Basemap(llcrnrlon=-119,llcrnrlat=22,urcrnrlon=-64,urcrnrlat=49, projection='lcc',lat_1=33,lat_2=45,lon_0=-95,resolution='c')
m.drawcoastlines()
m.drawstates()
m.drawcountries()
colors = iter(cm.rainbow(np.linspace(0, 1, communityCount)))
for partition in partition_modularity.community:
    color = next(colors)
    community = partition_modularity.community[partition]
    if len(community) >= 5:
        for county in community:
            x, y = m(G.vs[county]["longitude"],G.vs[county]["latitude"]) 
            m.scatter(x,y,3,marker='o',color=color)
plt.savefig('foo.png')

