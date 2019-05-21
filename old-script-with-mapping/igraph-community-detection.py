import igraph as ig
import louvain
import csv
import random
import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from mpl_toolkits.basemap import Basemap


def getMetadataFrom(filePath):
    """ Centers of Population from the U.S. Census Bureau: http://www2.census
    .gov/geo/docs/reference/cenpop2010/county/CenPop2010_Mean_CO.txt """
    metadata = {}
    with open(filePath) as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',', quoting=csv.QUOTE_NONE)
        for row in reader:
            statefp = row["STATEFP"].strip()
            countyfp = row["COUNTYFP"].strip()
            fips = statefp + countyfp
            lat = row["LATITUDE"].strip().replace("+", "")
            lng = row["LONGITUDE"].strip()
            countyName = row["COUNAME"].strip()
            stateName = row["STNAME"].strip()
            population = row["POPULATION"].strip()
            metadata[fips] = (lat, lng, countyName, stateName, population)
    return metadata


def getNodesEdgesAtMinimumWeightFrom(filePath, minimumWeight):
    nodes = []
    edges = []
    with open(filePath) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            fromCounty = row['fromCountyFIPSid']
            toCounty = row['toCountyFIPSid']
            fromState = fromCounty[0:1]
            toState = toCounty[0:1]
            # weight may also be set to the value of either
            # int(row['countTaxReturns'])
            # int(row['sumAdjustedGrossIncome1000s'])
            weight = int(row['countTaxExemptions'])
            if weight >= minimumWeight:
                nodes.append(fromCounty)
                nodes.append(toCounty)
                edges.append((fromCounty, toCounty, weight))
    nodes = set(nodes)  # omit duplicate node IDs
    return nodes, edges


def getGraphWithNodesEdgesMetadata(nodes, edges, metadata):
    graph = ig.Graph(directed=True)
    for node in nodes:
        lat = metadata[node][0]
        lng = metadata[node][1]
        countyName = metadata[node][2]
        stateName = metadata[node][3]
        population = metadata[node][4]
        graph.add_vertex(node, latitude=lat, longitude=lng,
                         countyName=countyName, stateName=stateName,
                         population=population)
    for edge in edges:
        graph.add_edge(edge[0], edge[1], weight=edge[2])
    return graph


def getGraphPartition(graph, resolution):
    """The returned partition is each county assigned to a community. While
    there are several methods available, RBConfiguration is tunable with a
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


def getDivergingColorList(numberOfColorsNeeded):
    """From the invaluable http://colorbrewer2.org using diverging data
    classes, colorblind safe for 3 and 4 colors, border context, terrain
    background. See also http://matplotlib.org/api/colors_api.html"""
    if numberOfColorsNeeded == 5:
        return ['#ca0020', '#f4a582', '#f7f7f7', '#92c5de', '#0571b0']
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


def drawMapOfSimilarityMatrix(graph, similarityMatrix, quality, targetCounty,
                              denominator, classesToDraw=5):
    if quality == 'high':
        basemapResolution = 'i'
        DPI = 500
        reliefScale = 1
        figSize = (10, 5)
    else:
        basemapResolution = 'c'
        DPI = 250
        reliefScale = 0.5
        figSize = (5, 2.5)

    plt.figure(figsize=figSize)
    m = Basemap(llcrnrlon=-119, llcrnrlat=22, urcrnrlon=-64, urcrnrlat=49,
                projection='lcc', lat_1=33, lat_2=45, lon_0=-95,
                resolution=basemapResolution)
    m.shadedrelief(scale=reliefScale)
    m.drawcoastlines()
    m.drawstates()
    m.drawcountries()
    if quality == 'high':
        m.drawcounties()

    toDraw = similarityMatrix[targetCounty]

    colors = getDivergingColorList(classesToDraw)
    classBucketSize = 1 / float(classesToDraw - 1)

    for county, matches in toDraw.iteritems():
        x, y = m(graph.vs.find(name=county)["longitude"],
                 graph.vs.find(name=county)["latitude"])
        percentSimilar = matches / float(denominator)
        if percentSimilar == 1:
            colorOffset = int(classesToDraw - 1)
        else:
            colorOffset = int(percentSimilar // classBucketSize)
        m.scatter(x, y, 3, marker='o', color=colors[colorOffset])

    mapName = "proportion-map-{0}-{1}.png".format(
        targetCounty, datetime.datetime.today())
    plt.savefig(mapName, dpi=DPI, bbox_inches='tight')


def getUniformDistributionMinMax(acceptableList, prevRes=1, prevMin=0.5,
                                 prevMax=1.5, numCommunitiesFound=10):
    coefficient = random.uniform(0.9, 1.1)
    if numCommunitiesFound < min(acceptableList):
        coefficient *= min(acceptableList) / float(numCommunitiesFound)
        print(" {0} found and {1} is the minimum OK community count".format(
            numCommunitiesFound, min(acceptableList)))
    elif numCommunitiesFound > max(acceptableList):
        coefficient *= max(acceptableList) / float(numCommunitiesFound)
        print(" {0} found and {1} is the maximum OK community count".format(
            numCommunitiesFound, max(acceptableList)))
    else:
        print("{0} is within the list of acceptable community counts".format(
            numCommunitiesFound))
    print("Modifying uniform distribution range by {0}".format(coefficient))
    return prevMin * coefficient, prevMax * coefficient


MINIMUM_EDGE_WEIGHT = 0  # import only edges at this weight or greater
MINIMUM_COMMUNITY_SIZE = 3  # draw communities at this size or greater
ACCEPTABLE_LIST_OF_NUMBER_OF_COMMUNITIES_FOUND = range(3, 7)
CREATE_THIS_MANY_RESULTS_FILES = 150
YEAR = "1213"  # 1112 for 2011-2012, 1213 for 2012-2013
TARGET_COUNTY = '46065'
MAP_QUALITY = 'high'

try:
    G = ig.Graph.Read_Pickle('persistentGraph-{0}-{1}.pickle'.format(
            YEAR, MINIMUM_EDGE_WEIGHT))
    print("Loaded graph from stored pickle file at {0}".format(
        datetime.datetime.today()))
    metadata = getMetadataFrom('government/CenPop2010_Mean_CO.txt')
    print("Loaded metadata at {0}".format(
        datetime.datetime.today()))
except Exception as e:
    print(e)
    metadata = getMetadataFrom('government/CenPop2010_Mean_CO.txt')
    print("Loaded metadata at {0}".format(
        datetime.datetime.today()))
    sourceFile = 'generated-datasets/county-to-county{0}.csv'.format(YEAR)
    nodes, edges = getNodesEdgesAtMinimumWeightFrom(
                                                sourceFile, MINIMUM_EDGE_WEIGHT)
    print("Loaded nodes and edges at {0}".format(
        datetime.datetime.today()))
    G = getGraphWithNodesEdgesMetadata(nodes, edges, metadata)
    print("Filled graph with nodes and edges at {0}".format(
        datetime.datetime.today()))
    G.write_pickle('persistentGraph-{0}-{1}.pickle'.format(
            YEAR, MINIMUM_EDGE_WEIGHT))
    print("Saved graph in stored pickle file at {0}".format(
        datetime.datetime.today()))

similarityMatrix = {}

print("Beginning community detection at {0}".format(datetime.datetime.today()))
distMin, distMax = getUniformDistributionMinMax(
            ACCEPTABLE_LIST_OF_NUMBER_OF_COMMUNITIES_FOUND)
for i in range(CREATE_THIS_MANY_RESULTS_FILES):
    numberOfCommunitiesDetected = 0
    while numberOfCommunitiesDetected not in \
            ACCEPTABLE_LIST_OF_NUMBER_OF_COMMUNITIES_FOUND:
        partitionResolution = random.uniform(distMin, distMax)
        partition = getGraphPartition(G, partitionResolution)
        numberOfCommunitiesDetected = getCountOfCommunitiesOfMinimumSize(
            partition, MINIMUM_COMMUNITY_SIZE)
        print("{0} communities found with resolution {1} at {2}".format(
            numberOfCommunitiesDetected, partitionResolution,
            datetime.datetime.today()))
        distMin, distMax = getUniformDistributionMinMax(
                ACCEPTABLE_LIST_OF_NUMBER_OF_COMMUNITIES_FOUND,
                partitionResolution, distMin, distMax,
                numberOfCommunitiesDetected)

    similarityMatrix = addResultsToSimilarityMatrix(G, partition,
                                                    MINIMUM_COMMUNITY_SIZE,
                                                    similarityMatrix)
    print("Updated similarityMatrix at {0}".format(datetime.datetime.today()))
    print("Completed {0} of {1} result files.".format(
                            (i+1), CREATE_THIS_MANY_RESULTS_FILES))

drawMapOfSimilarityMatrix(G, similarityMatrix, MAP_QUALITY, TARGET_COUNTY,
                          CREATE_THIS_MANY_RESULTS_FILES)
print("Mapped similarityMatrix at {0}".format(datetime.datetime.today()))
