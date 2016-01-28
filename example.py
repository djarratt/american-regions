#!/usr/bin/python
import igraph as ig
import logging
import louvain as louvain
import numpy as np
import matplotlib.pyplot as plt
from math import log10

def plot_graph(G, file, partition):
  ig.plot(G, target=file, vertex_color=partition.membership,
        mark_groups=zip(map(list, partition.community.values()), 
                        partition.community.keys()),
        vertex_frame_width=0,
        palette=ig.RainbowPalette(len(partition.community)))

f = open('output.txt', 'wb');


# Use n nodes in this example
n = 50;
# Generate some example graph (a tree in this case)
G = ig.Graph.Tree(n=n, children=3, type=ig.TREE_OUT);
# Initialise the optimiser, using default settings
opt = louvain.Optimiser();
# Find communities using CPM
p_cpm = opt.find_partition(G, partition_class=louvain.CPMVertexPartition,
    resolution=.1);
# Find communities using significance
p_sig = opt.find_partition(G, louvain.SignificanceVertexPartition);
# Find communities using modularity
p_mod = opt.find_partition(G, louvain.ModularityVertexPartition);

# Also add output to standard out
root = logging.getLogger()
root.setLevel(logging.DEBUG)
ch = logging.FileHandler('./pylouvain.log');
ch.setLevel(logging.DEBUG);
root.addHandler(ch)

# Find communities using modularity
p_mod = opt.find_partition(G, louvain.ModularityVertexPartition);
p_mod_rb = louvain.RBConfigurationVertexPartition(G, resolution=1, membership=p_mod.membership);

# Determine similarities between the three different partitions
f.writelines('NMI(mod, cpm)={0}\n'.format(p_mod.compare_to(p_cpm, method='nmi')));
f.writelines('NMI(mod, sig)={0}\n'.format(p_mod.compare_to(p_sig, method='nmi')));
f.writelines('NMI(sig, cpm)={0}\n'.format(p_sig.compare_to(p_cpm, method='nmi')));

f.writelines('Max Modularity={0}\n'.format(p_mod.modularity));
f.writelines('Max Significance={0}\n'.format(p_sig.significance()));

# Plot graphs
G['layout'] = G.layout_auto();
plot_graph(G, 'comm_cpm.pdf', p_cpm);
plot_graph(G, 'comm_mod.pdf', p_mod);
plot_graph(G, 'comm_sig.pdf', p_sig);

# Find all resolution values at which optimal partition
# changes using bisectioning.
res_results = opt.bisect(graph=G, 
                partition_class=louvain.CPMVertexPartition,
                resolution_range=(0,1));

# Plot number of internal edges versus resolution parameter
res_list = [(r,b_part.bisect_value) for r, b_part in res_results.iteritems()];
plt.step(zip(*res_list)[0], zip(*res_list)[1], where='post');
plt.xscale('log');
plt.xlabel('Resolution parameter');
plt.ylabel('Internal edges');
plt.savefig('testres.pdf');

# Plot all resolutions
max_d = int(log10(len(res_results))+1);
for ind, (res, part) in enumerate(res_results.iteritems()):
  plot_graph(G, 'comm_cpm_{0:0{width}}_{1}.pdf'.format(ind, res,
                     width=max_d), 
             part.partition);

# Find all resolution values at which optimal partition
# changes using bisectioning, but now use RB model with a
# configuration null model, i.e. modularity with a multiplicative
# linear resolution parameter.
res_results = opt.bisect(graph=G, 
                partition_class=louvain.RBConfigurationVertexPartition,
                resolution_range=(0,50));

# Plot all resolutions
max_d = int(log10(len(res_results))+1);
for ind, (res, part) in enumerate(res_results.iteritems()):
  plot_graph(G, 'comm_mod_{0:0{width}}_{1}.pdf'.format(ind, res,
                     width=max_d), 
             part.partition);

f.close();
