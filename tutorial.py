import igraph as ig
from string import ascii_uppercase
from random import choice, randrange
import louvain as louvain

def plot_graph(G, file, partition):
  ig.plot(G, target=file, vertex_color=partition.membership,
        mark_groups=zip(map(list, partition.community.values()), 
                        partition.community.keys()),
        vertex_frame_width=0,
        palette=ig.RainbowPalette(len(partition.community)))

G = ig.Graph(directed=True)

for letter in ascii_uppercase:
    G.add_vertex(letter)    

for i in range(100):
    L = ''
    M = ''
    while L == M:
        L = choice(ascii_uppercase)
        M = choice(ascii_uppercase)
    w = randrange(10) + 1
    G.add_edge(L, M, weight=w)

print(G)
print(G.is_weighted())
print("A" in G.vs["name"])

opt = louvain.Optimiser();
p_mod = opt.find_partition(G, louvain.ModularityVertexPartition);
p_mod_rb = louvain.RBConfigurationVertexPartition(G, resolution=1, membership=p_mod.membership);

G['layout'] = G.layout_auto();
plot_graph(G, 'tutorial_comm_mod.pdf', p_mod);


# name attribute of vertices will be the FIPS county ID
# also need latitude and longitude attributes
# use weight attribute for edges
# Graph.__init__(directed=True)
# can add edges using names!
# add_edge(fromName, toName, weight=1234)

