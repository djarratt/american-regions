# Fast unfolding of communities in large networks
# by Vincent D. Blondel, Jean-Loup Guillaume1, Renaud Lambiotte1 and Etienne Lefebvre
# http://arxiv.org/pdf/0803.0476.pdf
# Note this is for weighted undirected networks. There are several ways to convert directed to undirected graphs: http://igraph.org/r/doc/igraph-attribute-combination.html. I will choose sum.

import csv
import random
from collections import OrderedDict

nodes = []
edges = {}

sumOfAttachedWeights = {}
sumOfAllWeights = 0

nodeCommunity = {}
communityNodes = {}

def getCountOfNonEmptyCommunities():
    count = 0
    for community in communityNodes:
        if len(communityNodes[community]) > 0:
            count += 1
    return count

def getNodesByCommunity():
    global communityNodes
    communities = set(nodeCommunity.values())
    communityNodes = {}
    for node in nodeCommunity:
        community = nodeCommunity[node] 
        if community in communityNodes:
            communityNodes[community].append(node)
        else:
            communityNodes[community] = [node]

def modularity():
    summation = 0
    for community in communityNodes:
        nodesInThisCommunity = communityNodes[community]
        for node_i in nodesInThisCommunity:
            for node_j in nodesInThisCommunity:
                if node_i != node_j and node_i in edges and node_j in edges[node_i]:
                    weight_ij = edges[node_i][node_j]
                    sumOfAttached_i = sumOfAttachedWeights[node_i]
                    sumOfAttached_j = sumOfAttachedWeights[node_j]
                    toSum = weight_ij - float((sumOfAttached_i * sumOfAttached_j) / sumOfAllWeights)
                    # print("Comparing {0} and {1} = {2}".format(node_i, node_j, toSum))
                    summation += toSum       
    return float(summation / sumOfAllWeights)

def importNodesEdges(filepath):
    global sumOfAllWeights
    global sumOfAttachedWeights
    global nodes
    global edges
    
    with open(filepath) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            fromCounty = row['fromCountyFIPSid']
            toCounty = row['toCountyFIPSid']
            weight = int(row['countTaxExemptions'])
            sumOfAllWeights += weight
            
            nodes.append(fromCounty)
            nodes.append(toCounty)
            
            alreadyStoredInflow = 0
            if toCounty in edges:
                if fromCounty in edges[toCounty]:
                    alreadyStoredInflow = edges[toCounty][fromCounty]  
                    edges[toCounty][fromCounty] += weight
                
            if fromCounty not in edges:
                edges[fromCounty] = {toCounty: weight + alreadyStoredInflow}
            else:
                edges[fromCounty][toCounty] = weight + alreadyStoredInflow
                
            if fromCounty in sumOfAttachedWeights:
                sumOfAttachedWeights[fromCounty] += weight
            else:
                sumOfAttachedWeights[fromCounty] = weight
            if toCounty in sumOfAttachedWeights:
                sumOfAttachedWeights[toCounty] += weight
            else:
                sumOfAttachedWeights[toCounty] = weight        
            
    nodes = set(nodes)

def initialCommunityAssignment():
    global nodeCommunity
    communityId = 0
    for node in nodes:
        communityId += 1 # random.randrange(1, 11)
        nodeCommunity[node] = communityId
    getNodesByCommunity()
    
def sumOfEdgeWeightsCommunitySpecific(communityId):
    sumEdgeWeightsInsideCommunity = 0
    sumEdgeWeightsIncidentToNodesInCommunity = 0
    nodesInsideCommunity = communityNodes[communityId]
    for node in nodesInsideCommunity:
        if node in edges:
            edgesForThisNode = edges[node]
            for targetNode in edgesForThisNode:
                sumEdgeWeightsIncidentToNodesInCommunity += edgesForThisNode[targetNode]
                if targetNode in nodesInsideCommunity:
                    sumEdgeWeightsInsideCommunity += edgesForThisNode[targetNode]
    return sumEdgeWeightsInsideCommunity, sumEdgeWeightsIncidentToNodesInCommunity
    
def sumOfEdgeWeightsFromNodeToCommunity(node_i, communityId):
    sumFromNodeToCommunityNodes = 0
    if node_i in edges:
        edgesForThisNode = edges[node_i]
        for targetNode in edgesForThisNode:
            if nodeCommunity[targetNode] == communityId:
                sumFromNodeToCommunityNodes += edgesForThisNode[targetNode]
    return sumFromNodeToCommunityNodes

def moveNodesIntoBetterCommunities(iteration):
    #2. for each i, place it in neighbor j's community with best modularity improvement
    # gain in modularity moving node i into community C is given by
    # a = sum of edge weights inside C
    # b = sum of the weights of the edges from i to nodes in C
    # c = sum of the weights of the edges incident to nodes in C
    # d = sum of the weights of the edges incident to node i = sumOfAttachedWeights
    # Q = (a + b) / sumOfAllWeights
    # R = [(c + d) / sumOfAllWeights] ^ 2
    # S = a / sumOfAllWeights
    # T = (c / sumOfALlWeights) ^ 2
    # U = (d / sumOfAllWeights) ^ 2
    # solution = [Q - R] - [S - T - U]
    improvedNodes = 0
    for node in random.sample(nodes, len(nodes)):
        if node in edges:
            communityWithBestImprovement = None
            bestImprovement = 0.00001
            #currentModularity = modularity()
            currentCommunity = nodeCommunity[node]
            neighbors = edges[node].keys()
            for neighbor in random.sample(neighbors, len(neighbors)):
                neighborCommunity = nodeCommunity[neighbor]
                if currentCommunity != neighborCommunity:
                    #communityNodes[currentCommunity].remove(node)
                    #communityNodes[neighborCommunity].append(node)
                    a, c = sumOfEdgeWeightsCommunitySpecific(neighborCommunity)
                    b = sumOfEdgeWeightsFromNodeToCommunity(node, neighborCommunity)
                    d = sumOfAttachedWeights[node]
                    Q = float(a + b) / sumOfAllWeights
                    R = (float(c + d) / sumOfAllWeights)**2
                    S = float(a) / sumOfAllWeights
                    T = (float(c) / sumOfAllWeights)**2
                    U = (float(d) / sumOfAllWeights)**2
                    # print(a, b, c, d, Q, R, S, T, U)
                    improvement = (Q - R) - (S - T - U)
                    #improvement = modularity() - currentModularity
                    # print("Node {0} (community {1}) to neighbor {2} (community {3}) modularity move gain = {4}".format(node, currentCommunity, neighbor, neighborCommunity, improvement))
                    if improvement > bestImprovement:
                        bestImprovement = improvement
                        communityWithBestImprovement = neighborCommunity
                    #communityNodes[neighborCommunity].remove(node)
                    #communityNodes[currentCommunity].append(node)             
            if communityWithBestImprovement is not None and bestImprovement > 0:
                nodeCommunity[node] = communityWithBestImprovement
                communityNodes[currentCommunity].remove(node)
                communityNodes[communityWithBestImprovement].append(node)
                improvedNodes += 1
                # print("Moved node {0} to community {1}. Improvement {2} of round {3}.".format(node, communityWithBestImprovement, improvedNodes, iteration))
    return improvedNodes, iteration + 1
    
importNodesEdges('generated-datasets/county-to-county1213.csv')
initialCommunityAssignment()
improvedNodes = 1
iteration = 1
while improvedNodes > 0:
    improvedNodes, iteration = moveNodesIntoBetterCommunities(iteration)
    print("{0} non-empty communities.".format(getCountOfNonEmptyCommunities()))
print()
print(OrderedDict(sorted(communityNodes.viewitems(), key=lambda x: len(x[1]))))
print()
print(nodeCommunity)