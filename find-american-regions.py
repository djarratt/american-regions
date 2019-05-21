import pandas as pd
import igraph as ig
import random

STATE = 'New York'
COUNTY = 'New York'
ITERATIONS = 13

# get latitude and longitude values
county_locations = pd.read_csv("government/CenPop2010_Mean_CO.txt", dtype = str)
county_locations["fips"] = county_locations["STATEFP"] + county_locations["COUNTYFP"]

target_fips_to_map = county_locations[county_locations["STNAME"].str.startswith(STATE) &
                                      county_locations["COUNAME"].str.startswith(COUNTY)].iloc[0]["fips"]
print("FIPS code for {} County, {}, is {}".format(COUNTY, STATE, target_fips_to_map))                                   

# county to county migration data from IRS at
# https://www.irs.gov/statistics/soi-tax-stats-migration-data
# y1 means origin; y2 means destination
countyinflow1516 = pd.read_csv("government/irs/1516migrationdata/countyinflow1516.csv", dtype = str)
countyoutflow1516 = pd.read_csv("government/irs/1516migrationdata/countyoutflow1516.csv", dtype = str)
countyallflows = pd.concat([countyinflow1516, countyoutflow1516], sort = False)

# make FIPS codes single values instead of separate columns
countyallflows["y1_fips"] = countyallflows["y1_statefips"] + countyallflows["y1_countyfips"]
countyallflows["y2_fips"] = countyallflows["y2_statefips"] + countyallflows["y2_countyfips"]

# filter data
filtered_flows = countyallflows[
# 1) omit aggregation rows
    ~countyallflows["y1_countyfips"].str.startswith("000") &
    ~countyallflows["y2_countyfips"].str.startswith("000") &
# 2) omit non-USA rows
    ~countyallflows["y1_statefips"].str.startswith("9") &
    ~countyallflows["y2_statefips"].str.startswith("9")]\
    .replace("-1", "10") # inpute over suppressed rows with halfway point between 0 and 20

# separate into migrants versus non-migrants
# and keep only 'n2' (number of tax exemptions, a proxy for person count)
# dropping duplicates because inflow and outflow files overlap quite a bit
nonmigrants = filtered_flows[filtered_flows["y1_fips"] == filtered_flows["y2_fips"]]\
    [["y2_fips", "n2"]].drop_duplicates()
migrants = filtered_flows[filtered_flows["y1_fips"] != filtered_flows["y2_fips"]]\
    [["y1_fips", "y2_fips", "n2"]].drop_duplicates()
    
# prepare graph edges
edges = migrants.merge(nonmigrants, on = "y2_fips")
edges["weight"] = 100 * (pd.to_numeric(edges["n2_x"]) / pd.to_numeric(edges["n2_y"]))
edges = edges[["y1_fips", "y2_fips", "weight"]]\
    .rename(index=str, columns={"y1_fips": "from", "y2_fips": "to"})

fips_found_in_same_region = {}
for i in range(ITERATIONS):
    iteration_sample_frac = random.uniform(0.1, 0.9)
    print("Iteration {} of {}: sampling percent {}".format(i + 1, ITERATIONS, iteration_sample_frac))
    # instantiate graph via sampling edges
    # smaller frac value means faster graph community detection, but the communities themselves
    # may be qualitatively different. so choose from a variety of fraction values.
    edge_tuples = [tuple(x) for x in edges.sample(frac=iteration_sample_frac).values]
    G = ig.Graph.TupleList(edge_tuples, directed = True, edge_attrs = ['weight'])
    G.to_undirected(mode="collapse", combine_edges='sum')
    # find partitions
    partitions_found = G.community_multilevel(weights = 'weight')
    communities_df = pd.DataFrame()
    for clid, cluster in enumerate(partitions_found):
        for member in cluster:
            communities_df = communities_df.append(
                pd.DataFrame.from_dict({'region': [clid], 'fips': [G.vs[member]['name']]})
            )
    #print(communities_df['region'].value_counts())

    target_region = communities_df[communities_df["fips"].str.startswith(target_fips_to_map)].iloc[0]["region"]
    other_fips_in_region = communities_df[communities_df["region"] == target_region]["fips"]
    for neighbor_fips in other_fips_in_region:
        if neighbor_fips not in fips_found_in_same_region:
            fips_found_in_same_region[neighbor_fips] = 1
        else:
            fips_found_in_same_region[neighbor_fips] += 1

target_fips_neighbors = pd.DataFrame(list(fips_found_in_same_region.items()), columns = ["fips", "frequency"])\
    .merge(county_locations, on = 'fips')

# omit neighbors that only appear once -- likely noise
target_fips_neighbors[target_fips_neighbors["frequency"] > 1]\
    .sort_values(by = ["frequency", "fips"], ascending = [False, True])\
    .to_csv("neighbor-fips-to-{}.csv".format(target_fips_to_map))