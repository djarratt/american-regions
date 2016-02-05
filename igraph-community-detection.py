import igraph as ig
import louvain
import csv
import random
import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from mpl_toolkits.basemap import Basemap


def getGeoCoordinatesFrom(filePath):
    """ Centers of Population from the U.S. Census Bureau: http://www2.census
    .gov/geo/docs/reference/cenpop2010/county/CenPop2010_Mean_CO.txt """
    geo_coordinates = {}
    with open(filePath) as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',', quoting=csv.QUOTE_NONE)
        for row in reader:
            statefp = row["STATEFP"].strip()
            countyfp = row["COUNTYFP"].strip()
            fips = statefp + countyfp
            lat = row["LATITUDE"].strip().replace("+", "")
            lng = row["LONGITUDE"].strip()
            geo_coordinates[fips] = (lat, lng)
    return geo_coordinates


def getNodesEdgesAtMinimumWeightFrom(filePath, minimumWeight):
    nodes = []
    edges = []
    with open(filePath) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            fromCounty = row['fromCountyFIPSid']
            toCounty = row['toCountyFIPSid']
            # weight may also be set to the value of either
            # int(row['countTaxReturns'])
            # int(row['sumAdjustedGrossIncome1000s'])
            weight = int(row['countTaxExemptions'])
            if weight >= minimumWeight:
                nodes.append(fromCounty)
                nodes.append(toCounty)
                edges.append((fromCounty, toCounty, weight))

    # omit duplicate node IDs
    nodes = set(nodes)
    return nodes, edges


def getGraphWithNodesEdgesGeoCoordinates(nodes, edges, geo_coordinates):
    graph = ig.Graph(directed=True)
    for node in nodes:
        lat = geo_coordinates[node][0]
        lng = geo_coordinates[node][1]
        graph.add_vertex(node, latitude=lat, longitude=lng)
    for edge in edges:
        graph.add_edge(edge[0], edge[1], weight=edge[2])
    return graph


def writeResultsToFile(results, filePath):
    with open(filePath, 'wb') as csvfile:
        fieldnames = ['counties']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for community in results:
            writer.writerow({'counties': community})


def getGraphPartition(graph, resolution):
    """The returned partition is each county assigned to a community. While
    there are several methods available, RBConfiguration is tunable with the
    resolution parameter. Bigger resolutions mean smaller communities. Smaller
    resolutions mean fewer communities."""
    return louvain.find_partition(G, method='RBConfiguration', weight='weight',
                                  resolution_parameter=resolution)


def getCountOfCommunitiesOfMinimumSize(partition, minimumSize):
    count = 0
    for community in partition:
        if len(community) >= minimumSize:
            count += 1
    return count


def getQualitativeColorList(numberOfColorsNeeded):
    """From the invaluable http://colorbrewer2.org using qualitative data
    classes, colorblind safe for 3 and 4 colors, border context, terrain
    background. See also http://matplotlib.org/api/colors_api.html"""
    if numberOfColorsNeeded == 3:
        return ['#1b9e77', '#d95f02', '#7570b3']
    elif numberOfColorsNeeded == 4:
        return ['#a6cee3', '#1f78b4', '#b2df8a', '#33a02c']
    elif numberOfColorsNeeded == 5:
        return ['#1b9e77', '#d95f02', '#7570b3', '#e7298a', '#66a61e']
    elif numberOfColorsNeeded == 6:
        return ['#1b9e77', '#d95f02', '#7570b3', '#e7298a', '#66a61e',
                '#e6ab02']
    elif numberOfColorsNeeded == 7:
        return ['#1b9e77', '#d95f02', '#7570b3', '#e7298a', '#66a61e',
                '#e6ab02', '#a6761d']
    else:
        return iter(cm.rainbow(np.linspace(0, 1, numberOfColorsNeeded)))


def addResultsToSimilarityMatrix(graph, partition, minimumSize,
                                 similarityMatrix):
    for community in partition:
        communityList = []
        if len(community) > minimumSize:
            for county in community:
                thisFIPS = graph.vs[county]["name"]
                communityList.append(thisFIPS)
            for county1 in communityList:
                for county2 in communityList:
                    if county1 not in similarityMatrix:
                        similarityMatrix[county1] = {}
                        similarityMatrix[county1][county2] = 1
                    elif county2 not in similarityMatrix[county1]:
                        similarityMatrix[county1][county2] = 1
                    else:
                        similarityMatrix[county1][county2] += 1
    return similarityMatrix


def drawMapOfPartition(partition, quality, minimumSize, graph):
    if quality == 'high':
        basemapResolution = 'i'
        DPI = 500
        reliefScale = 1
        figSize = (10, 5)
    else:
        basemapResolution = 'c'
        DPI = 100
        reliefScale = 0.2
        figSize = (4, 2)

    plt.figure(figsize=figSize)
    m = Basemap(llcrnrlon=-119, llcrnrlat=22, urcrnrlon=-64, urcrnrlat=49,
                projection='lcc', lat_1=33, lat_2=45, lon_0=-95,
                resolution=basemapResolution)
    m.shadedrelief(scale=reliefScale)
    m.drawcoastlines()
    m.drawstates()
    m.drawcountries()
    if quality == 'high':
        m.drawrivers(color='blue')
        m.drawcounties()

    numberOfCommunitiesDetected = getCountOfCommunitiesOfMinimumSize(
                                    partition, minimumSize)
    colors = getQualitativeColorList(numberOfCommunitiesDetected)
    for community in partition:
        color = next(colors)
        if len(community) >= minimumSize:
            for county in community:
                x, y = m(graph.vs[county]["longitude"],
                         graph.vs[county]["latitude"])
                m.scatter(x, y, 3, marker='o', color=color)

    mapName = "maps/american-regions-{0}-{1}-{2}.png".format(
                datetime.datetime.today(), res, numberOfCommunitiesDetected)
    plt.savefig(mapName, dpi=DPI, bbox_inches='tight')


def drawMapOfSimilarityMatrix(graph, similarityMatrix, quality, targetCounty,
                              denominator):
    if quality == 'high':
        basemapResolution = 'i'
        DPI = 500
        reliefScale = 1
        figSize = (10, 5)
    else:
        basemapResolution = 'c'
        DPI = 100
        reliefScale = 0.2
        figSize = (4, 2)

    plt.figure(figsize=figSize)
    m = Basemap(llcrnrlon=-119, llcrnrlat=22, urcrnrlon=-64, urcrnrlat=49,
                projection='lcc', lat_1=33, lat_2=45, lon_0=-95,
                resolution=basemapResolution)
    m.shadedrelief(scale=reliefScale)
    m.drawcoastlines()
    m.drawstates()
    m.drawcountries()
    if quality == 'high':
        m.drawrivers(color='blue')
        m.drawcounties()

    toDraw = similarityMatrix[targetCounty]

    for county, matches in toDraw.iteritems():
        x, y = m(graph.vs.find(name=county)["longitude"],
                 graph.vs.find(name=county)["latitude"])
        m.scatter(x, y, 3, marker='o', color=str((matches/float(denominator))))

    mapName = "proportion-map-{0}-{1}.png".format(
        targetCounty, datetime.datetime.today())
    plt.savefig(mapName, dpi=DPI, bbox_inches='tight')


MINIMUM_EDGE_WEIGHT = 0  # import only edges at this weight or greater
MINIMUM_COMMUNITY_SIZE = 3  # draw communities at this size or greater
ACCEPTABLE_LIST_OF_NUMBER_OF_COMMUNITIES_FOUND = [4]
CREATE_THIS_MANY_RESULTS_FILES = 3

try:
    G = ig.Graph.Read_Pickle('persistentGraph.pickle')
    print("Loaded graph from stored pickle file at {0}".format(
        datetime.datetime.today()))
except Exception as e:
    print(e)
    geo_coordinates = getGeoCoordinatesFrom('government/CenPop2010_Mean_CO.txt')
    print("Loaded geo coordinates at {0}".format(
        datetime.datetime.today()))
    nodes, edges = getNodesEdgesAtMinimumWeightFrom(
                                'generated-datasets/county-to-county1213.csv',
                                MINIMUM_EDGE_WEIGHT)
    print("Loaded nodes and edges at {0}".format(
        datetime.datetime.today()))
    G = getGraphWithNodesEdgesGeoCoordinates(nodes, edges, geo_coordinates)
    print("Filled graph with nodes and edges at {0}".format(
        datetime.datetime.today()))
    G.write_pickle('persistentGraph.pickle')
    print("Saved graph in stored pickle file at {0}".format(
        datetime.datetime.today()))

similarityMatrix = {}

print("Beginning community detection at {0}".format(datetime.datetime.today()))
for i in range(CREATE_THIS_MANY_RESULTS_FILES):
    numberOfCommunitiesDetected = 0
    while numberOfCommunitiesDetected not in \
            ACCEPTABLE_LIST_OF_NUMBER_OF_COMMUNITIES_FOUND:

        partitionResolution = random.uniform(0.225, 0.3)
        partition = getGraphPartition(G, partitionResolution)
        numberOfCommunitiesDetected = getCountOfCommunitiesOfMinimumSize(
            partition, MINIMUM_COMMUNITY_SIZE)
        print("{0} communities found with resolution {1} at {2}".format(
            numberOfCommunitiesDetected, partitionResolution,
            datetime.datetime.today()))

    #results = getListOfCommunities(G, partition, MINIMUM_COMMUNITY_SIZE)
    #print("Created results data structure at {0}".format(
    #    datetime.datetime.today()))
    # drawMapOfPartition(partition, 'crude', MINIMUM_COMMUNITY_SIZE, graph)

    similarityMatrix = addResultsToSimilarityMatrix(G, partition,
                                                    MINIMUM_COMMUNITY_SIZE,
                                                    similarityMatrix)
    print("Updated similarityMatrix at {0}".format(datetime.datetime.today()))
    #writeResultsToFile(results,
    #                   'results-{0}-{1}-{2}.csv'.format(
    #                        i, partitionResolution, datetime.datetime.today()))
    #print("Wrote results to CSV file at {0}".format(datetime.datetime.today()))
    print("Completed {0} of {1} results files.".format(
                            (i+1), CREATE_THIS_MANY_RESULTS_FILES))

drawMapOfSimilarityMatrix(G, similarityMatrix, 'crude', '17031',
                          CREATE_THIS_MANY_RESULTS_FILES)
print("Mapped similarityMatrix at {0}".format(datetime.datetime.today()))
