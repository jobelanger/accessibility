# -*- coding: utf-8 -*-
"""
Created on Sun Jun 30 18:10:42 2019

Full script for network analysis in Puerto Rico.

Measuring travel time from all Point A's (~1 mil WorldPop points) to 5 key services of interest:
    dialysis facilities
    hospitals
    pharmacies
    gas stations
    K-12 public schools

Travel time is measured as the walking time (accounting for slope) from Point A to the closest node 
on the road network, plus driving time from there to the closest road node to a service.
Services are expected to be proximal to the road network, so no measure is taken between 
road and service.

From the origin-destination matrix of all points of origin to all services, filtering for
the first, second, and third shortest trip. This simulates the travel time if your closest facility 
were out of service, e.g. due to storm disruption.
"""

#%%
"""
Configure script.

"""
# Note: gostnet.py is in the working directory folder.
import os, sys
gostNetsFolder = os.path.dirname(os.getcwd())
sys.path.insert(0, gostNetsFolder)
import GOSTnet as gn
import pandas as pd
from geopandas import GeoDataFrame
import shapely
from shapely.geometry import Point, box
import geopandas as gpd
import osmnx as ox
import networkx as nx
import numpy as np
import rasterio as rt

# Didn't use:
import fiona
import peartree
from osgeo import gdal
import importlib
import matplotlib.pyplot as plt
import subprocess, glob

pth = os.path.join(gostNetsFolder, "SampleData")

pd.set_option('display.max_columns', 30)

#%% 
"""
Prepare and clean the data.

"""

# OSM road network is in WGS84. Projected each dataset to match.
# Multi-point shapefiles don't read well. Re-created shapefile from csv with geopandas for each offending file.

dfH = os.path.join(gostNetsFolder, "SampleData", "hospitals1.csv")
dfH = pd.read_csv(dfH)
geometry = [Point(xy) for xy in zip(dfH.X, dfH.Y)]
crs = {'init': 'epsg:4326'} 
inH = GeoDataFrame(dfH, crs=crs, geometry=geometry)
inH.to_file(driver='ESRI Shapefile', filename='hospitals2.shp') 
# 75 observations.

dfD = os.path.join(gostNetsFolder, "SampleData", "dialysis2.csv")
dfD = pd.read_csv(dfD)
geometry = [Point(xy) for xy in zip(dfD.long, dfD.lat)]
crs = {'init': 'epsg:4326'} 
inD = GeoDataFrame(dfD, crs=crs, geometry=geometry)
inD.to_file(driver='ESRI Shapefile', filename='dialysis2wgs84.shp') 
# Original dataset had 47 individual observations. Two of these were duplicates, making 45 total.

dfG = os.path.join(gostNetsFolder, "SampleData", "gas3.csv")
dfG = pd.read_csv(dfG)
geometry = [Point(xy) for xy in zip(dfG.X, dfG.Y)]
crs = {'init': 'epsg:4326'} 
inG = GeoDataFrame(dfG, crs=crs, geometry=geometry)
inG.to_file(driver='ESRI Shapefile', filename='gas4wgs84.shp') 
# 323 observations.

dfP = os.path.join(gostNetsFolder, "SampleData", "pharmacies1.csv")
dfP = pd.read_csv(dfP)
geometry = [Point(xy) for xy in zip(dfP.X, dfP.Y)]
crs = {'init': 'epsg:4326'} 
inP = GeoDataFrame(dfP, crs=crs, geometry=geometry)
inP.to_file(driver='ESRI Shapefile', filename='pharm3wgs84.shp') 
# 965 observations.

dfE = os.path.join(gostNetsFolder, "SampleData", "education3.csv")
dfE = pd.read_csv(dfE)
geometry = [Point(xy) for xy in zip(dfE.X, dfE.Y)]
crs = {'init': 'epsg:4326'} 
inE = GeoDataFrame(dfE, crs=crs, geometry=geometry)
inE.to_file(driver='ESRI Shapefile', filename='education3wgs84.shp') 
# 1,456 observations.

dfO = os.path.join(gostNetsFolder, "SampleData", "wpop1.csv")
dfO = pd.read_csv(dfO)
geometry = [Point(xy) for xy in zip(dfO.X, dfO.Y)]
crs = {'init': 'epsg:4326'} 
inO = GeoDataFrame(dfO, crs=crs, geometry=geometry)
inO.to_file(driver='ESRI Shapefile', filename='wpop2wgs84.shp') 
# All cleaning for WorldPop detailed below was done in R and QGIS:
# 1,082,378 original observations. Removed observations where population = 0, leaving 1,075,783 observations. 
    # tidyverse filter()
# Each WorldPop feature is assigned a unique ID ("wid") and its corresponding municipal ID ("mid") and municipio name.
    # 1:nrow()
    # Spatial join in QGIS (note: some coastal points fall outside of the municipio boundaries. To resolve,
        # created a buffer of all municipal features, and merged those buffer zones onto the municipalities 
        # polygon shapefile.)



#%%
"""
If starting new session, load the cleaned data from disk.
"""
inputOrigins = os.path.join(gostNetsFolder, "SampleData", "wpop3wgs84.shp")
inputD = os.path.join(gostNetsFolder, "SampleData", "dialysis2wgs84.shp")
inputH = os.path.join(gostNetsFolder, "SampleData", "hospitals2.shp")
inputG = os.path.join(gostNetsFolder, "SampleData", "gas4wgs84.shp")
inputP = os.path.join(gostNetsFolder, "SampleData", "pharm3wgs84.shp")
inputE = os.path.join(gostNetsFolder, "SampleData", "education3wgs84.shp")

inO = gpd.read_file(inputOrigins) # Around 1 million rows
inD = gpd.read_file(inputD) # 45 rows
inH = gpd.read_file(inputH) # 75 rows
inG = gpd.read_file(inputG) # Around 300 rows
inP = gpd.read_file(inputP) # Around 1000 rows
inE = gpd.read_file(inputE) # Around 1500 rows
networkType = 'drive'


# Generate shape from shapefile for the bounding box
aoi = r'prboundingwgs84.shp' 
# Graph didn't populate on the smaller islands when using the Puerto Rico admin boundary.
# Created a rectangular bounding box (in QGIS) to use as the AOI instead.
shp = gpd.read_file(os.path.join(pth, aoi))
bound = shp.geometry.iloc[0]
bound # Check that it's a rectangle (short and wide)

#%%
""" 
Get driving network for all islands in Puerto Rico. 

Travel measured in length (meters).

"""

gDrive = ox.graph_from_polygon(bound, network_type= 'drive')
# This took about half an hour.
# Note: length is measured in meters.

# Save all road nodes (points on the road) to file.
gDrive_node_gdf = gn.node_gdf_from_graph(gDrive)
gDrive_node_gdf.to_csv(os.path.join(pth, 'drive_dist_node.csv'))


#%% 
"""
Add a time measure using a speed dictionary.

"""

speed_dict = {
                'residential': 20,  # kmph
                'primary': 40, # kmph
                'primary_link':35,
                'motorway':45,
                'motorway_link': 40,
                'trunk': 40,
                'trunk_link':35,
                'secondary': 30, # kmph
                'secondary_link':25,
                'tertiary':30,
                'tertiary_link': 25,
                'unclassified':20, 
                'road':20,
                'crossing':20,
                'living_street':20
                }
gTime = gn.convert_network_to_time(gDrive, distance_tag = 'length', graph_type = networkType, speed_dict = speed_dict)
# Note: time is in seconds.

# Save road nodes and road edges to file. Edges contains time measure.
edges = gn.edge_gdf_from_graph(gTime)
nodes = gn.node_gdf_from_graph(gTime)
edges.to_csv(os.path.join(pth, 'drive_time_edge.csv'))
nodes.to_csv(os.path.join(pth, 'drive_time_node.csv'))
# 171,222 road nodes 


# Save a pickle of the graph with the time measure for easy recall.
gn.save(gTime, 'gTime', '', edges = False, nodes = False)


#%% If starting new session, reload graph from file
gTime = nx.read_gpickle("gTime.pickle")


#%%
"""
Origins and destinations

Measure distance from origin/destination to nearest node and save to file.

"""

# pandana_snap calculates the great circle distance between the origin and nearest road node.
# Took maybe 20 min for Origins. Much shorter for the rest.
# Adding x,y fields on origins file for later use with add_elevation function.
inO['x'] = inO['geometry'].x
inO['y'] = inO['geometry'].y
inOsnap = gn.pandana_snap(gTime, inO, source_crs = 'epsg:4326', target_crs = 'epsg:3920', add_dist_to_node_col = True)
inOsnap.to_csv('inOsnap.csv', index=True)

inDsnap = gn.pandana_snap(gTime, inD, source_crs = 'epsg:4326', target_crs = 'epsg:3920', add_dist_to_node_col = True)
inDsnap.to_csv('inDsnap.csv', index=True)
inHsnap = gn.pandana_snap(gTime, inH, source_crs = 'epsg:4326', target_crs = 'epsg:3920', add_dist_to_node_col = True)
inHsnap.to_csv('inHsnap.csv', index=True)
inGsnap = gn.pandana_snap(gTime, inG, source_crs = 'epsg:4326', target_crs = 'epsg:3920', add_dist_to_node_col = True)
inGsnap.to_csv('inGsnap.csv', index=True)
inPsnap = gn.pandana_snap(gTime, inP, source_crs = 'epsg:4326', target_crs = 'epsg:3920', add_dist_to_node_col = True)
inPsnap.to_csv('inPsnap.csv', index=True)
inEsnap = gn.pandana_snap(gTime, inE, source_crs = 'epsg:4326', target_crs = 'epsg:3920', add_dist_to_node_col = True)
inEsnap.to_csv('inEsnap.csv', index=True)



# Save to file
inOsnap.to_csv(os.path.join(pth, 'inOsnap.csv'))
inDsnap.to_csv(os.path.join(pth, 'inDsnap.csv'))
inHsnap.to_csv(os.path.join(pth, 'inHsnap.csv'))
inGsnap.to_csv(os.path.join(pth, 'inGsnap.csv'))
inPsnap.to_csv(os.path.join(pth, 'inPsnap.csv'))
inEsnap.to_csv(os.path.join(pth, 'inEsnap.csv'))



#%% If already created, load from file.
inOsnap = os.path.join(gostNetsFolder, "SampleData", "inOsnap.csv")
inOsnap = pd.read_csv(inOsnap)
inDsnap = os.path.join(gostNetsFolder, "SampleData", "inDsnap.csv")
inDsnap = pd.read_csv(inDsnap)
inHsnap = os.path.join(gostNetsFolder, "SampleData", "inHsnap.csv")
inHsnap = pd.read_csv(inHsnap)
inGsnap = os.path.join(gostNetsFolder, "SampleData", "inGsnap.csv")
inGsnap = pd.read_csv(inGsnap)
inPsnap = os.path.join(gostNetsFolder, "SampleData", "inPsnap.csv")
inPsnap = pd.read_csv(inPsnap)
inEsnap = os.path.join(gostNetsFolder, "SampleData", "inEsnap.csv")
inEsnap = pd.read_csv(inEsnap)




#%%
"""
Map elevation onto road nodes and points of origin

"""
# If starting new session, load road nodes from disk.
nodes = os.path.join(gostNetsFolder, "SampleData", "drive_time_node.csv")
nodes = gpd.read_file(nodes)

#%%

# Ensure nodes coordinates and unique ID field are in the right data type.
nodes['x'] = nodes['x'].astype('float')
nodes['y'] = nodes['y'].astype('float')
nodes['osmid'] = nodes['osmid'].astype(int)


def add_elevation(df, x, y, srtm_pth):
    # walk all tiles, find path

    tiles = []
    for root, folder, files in os.walk(os.path.join(srtm_pth,'high_res')):
        for f in files:
            if f[-3:] == 'hgt':
                tiles.append(f[:-4])

    # load dictionary of tiles
    arrs = {}
    for t in tiles:
         arrs[t] = rt.open(srtm_pth+r'\high_res\{}.hgt\{}.hgt'.format(t, t), 'r')
    # assign a code
    uniques = []
    df['code'] = 'placeholder'
    def tile_code(z):
        E = str(abs(z[x])+1)[:2]
        N = str(abs(z[y]))[:2]
        return 'N{}W0{}'.format(N, E)
    df['code'] = df.apply(lambda z: tile_code(z), axis = 1)
    unique_codes = list(set(df['code'].unique()))

    z = {}
    # Match on High Precision Elevation
    property_name = 'elevation'
    for code in unique_codes:

        df2 = df.copy()
        df2 = df2.loc[df2['code'] == code]
        dataset = arrs[code]
        b = dataset.bounds
        datasetBoundary = box(b[0], b[1], b[2], b[3])
        selKeys = []
        selPts = []
        for index, row in df2.iterrows():
            selPts.append((row[x],row[y]))
            selKeys.append(index)
        raster_values = list(dataset.sample(selPts))
        raster_values = [x[0] for x in raster_values]
        # generate new dictionary of {node ID: raster values}
        z.update(zip(selKeys, raster_values))
    
    elev_df = pd.DataFrame.from_dict(z, orient='index')
    elev_df.columns = ['elevation']
    
    missing = elev_df.copy()
    missing = missing.loc[missing.elevation < 0]
    
    print('missing: %s' % len(missing))
    
    if len(missing) > 0:
        missing_df = df.copy()
        missing_df = missing_df.loc[missing.index]
        low_res_tifpath = os.path.join(srtm_pth, 'clipped', 'W100N40.GIF')
        dataset = rt.open(low_res_tifpath, 'r')
        b = dataset.bounds
        datasetBoundary = box(b[0], b[1], b[2], b[3])
        selKeys = []
        selPts = []
        for index, row in missing_df.iterrows():
            if Point(row[x], row[y]).intersects(datasetBoundary):
                selPts.append((row[x],row[y]))
                selKeys.append(index)
        raster_values = list(dataset.sample(selPts))
        raster_values = [x[0] for x in raster_values]
        z.update(zip(selKeys, raster_values))

        elev_df = pd.DataFrame.from_dict(z, orient='index')
        elev_df.columns = ['elevation']
    df['point_elev'] = elev_df['elevation']
    df = df.drop('code', axis = 1)
    return df


nodes_elev = add_elevation(nodes, "x", "y", pth) # Takes a few minutes.

# Origin points are different from road nodes. Need elevation for both.
# Using inOsnap was giving the error: 'Series' object has no attribute 'x'. 
    # To work around this, merged the new NN fields from snap onto the original inO.
inO.dtypes
inOsnap2 = pd.merge(inO[['wpop', 'xmid', 'wid', 'municipio', 'geometry', 'x', 'y']], 
                    inOsnap[['wid', 'NN', 'NN_dist']], on='wid', how='left')
inOsnap2.dtypes
inOsnap2.isna().sum()
O_elev = add_elevation(inOsnap2, "x", "y", pth) # Started 11:21pm


# Save to file.
nodes_elev.to_csv(os.path.join(pth, 'nodes_elev.csv'))
O_elev.to_csv(os.path.join(pth, 'O_elev.csv'))


#%% Reload from disk.
nodes_elev = os.path.join(pth, "nodes_elev.csv")
nodes_elev = gpd.read_file(nodes_elev)
O_elev = os.path.join(pth, "O_elev.csv")
O_elev = gpd.read_file(O_elev)


#%% 

"""
Elevation-adjusted walk time to road.

"""

# generate_walktimes function takes a single dataframe, and all numbers must be float.
# Merging the two datasets and cleaning up any naming issues.
nodes_elev.rename(columns={'node_ID':'NN'}, inplace=True)
zvalues = pd.merge(O_elev, nodes_elev, on='NN', how='left')
zvalues.head(5)
zvalues.rename(columns={'point_elev_y':'node_elev'}, inplace=True)
zvalues.dtypes
zvalues['point_elev'] = zvalues['point_elev'].astype(float)


# Time is in seconds.
def generate_walktimes(df, start = 'point_elev', end = 'node_elev', dist = 'NN_dist', max_walkspeed = 6, min_speed = 0.1):
    # Tobler's hiking function: https://en.wikipedia.org/wiki/Tobler%27s_hiking_function
    def speed(incline_ratio, max_speed):
        walkspeed = max_speed * np.exp(-3.5 * abs(incline_ratio + 0.05)) 
        return walkspeed

    speeds = {}
    times = {}

    for index, data in df.iterrows():
        if data[dist] > 0:
            delta_elevation = data[end] - data[start]
            incline_ratio = delta_elevation / data[dist]
            speed_kmph = speed(incline_ratio = incline_ratio, max_speed = max_walkspeed)
            speed_kmph = max(speed_kmph, min_speed)
            speeds[index] = (speed_kmph)
            times[index] = (data[dist] / 1000 * 3600 / speed_kmph)

    speed_df = pd.DataFrame.from_dict(speeds, orient = 'index')
    time_df = pd.DataFrame.from_dict(times, orient = 'index')

    df['walkspeed'] = speed_df[0]
    df['walk_time'] = time_df[0]
    
    return df

zwalk = generate_walktimes(zvalues) # Takes about 5 minutes.
zwalk.head(5)
zwalk.to_csv('zwalk_full.csv', index=True) # Takes a few minutes.


# Clean up the file for only the necessary columns.
zwalk2 = zwalk.drop(columns=['geometry_x', 'x_x', 'y_x', 'NN_dist', 'point_elev', 
                                   'x_y', 'y_y', 'ref', 'highway', 'geometry_y', 'node_elev'])
zwalk2.dtypes

# Convert from seconds to minutes
zwalk2['walk_time'] = zwalk2['walk_time'] / 60 
zwalk2.head()

# Save to disk.
zwalk2.to_csv('zwalk.csv', index=True)



#%% 
"""
Create origin-destination accessibility scores for the nodes nearest to each service.

"""

# Using calculate_OD
# We only need to find the origin-destination pairs for nodes closest to the origins and services,
# and some nodes will be the nearest for more than one service.
origins = list(inOsnap.NN.unique())
listD = list(inDsnap.NN.unique()) 
listH = list(inHsnap.NN.unique()) 
listG = list(inGsnap.NN.unique()) 
listP = list(inPsnap.NN.unique()) 
listE = list(inEsnap.NN.unique())
destslist = listD + listH + listG + listP + listE
dests = list(set(destslist))
len(dests) # There are 2,700 unique nearest nodes.
fail_value = 999999999 # If there is no shortest path, the OD pair will be assigned the fail value.

OD = gn.calculate_OD(gTime, origins, dests, fail_value, weight = 'time')
ODdf = pd.DataFrame(OD, index = origins, columns = dests)
# Full 5 variable list (dests) takes about 2 hours.
# Created a 141873 x 2700 matrix

# Convert to minutes and save to file.
ODdf.head(5)
ODmin = ODdf[ODdf <fail_value] / 60
ODdf.to_csv(os.path.join(pth, 'OD.csv'))


# Create POI-specific OD and save to file.
ODD = ODdf.loc[:, listD]
ODD = ODD[ODD < fail_value] / 60 
ODD.to_csv(os.path.join(pth, 'ODD.csv')) # Each takes less than a minute.

ODH = ODdf.loc[:, listH]
ODH = ODH[ODH < fail_value] / 60 
ODH.to_csv(os.path.join(pth, 'ODH.csv'))

ODG = ODdf.loc[:, listG]
ODG = ODG[ODG < fail_value] / 60 
ODG.to_csv(os.path.join(pth, 'ODG.csv'))

ODP = ODdf.loc[:, listP]
ODP = ODP[ODP < fail_value] / 60 
ODP.to_csv(os.path.join(pth, 'ODP.csv'))

ODE = ODdf.loc[:, listE]
ODE = ODE[ODE < fail_value] / 60 
ODG.to_csv(os.path.join(pth, 'ODE.csv'))


#%% 
# If starting new session, reload from disk.
ODD = os.path.join(gostNetsFolder, "SampleData", "ODD.csv")
ODD = pd.read_csv(ODD)
ODH = os.path.join(gostNetsFolder, "SampleData", "ODH.csv")
ODH = pd.read_csv(ODH)
ODG = os.path.join(gostNetsFolder, "SampleData", "ODG.csv")
ODG = pd.read_csv(ODG)
ODP = os.path.join(gostNetsFolder, "SampleData", "ODP.csv")
ODP = pd.read_csv(ODP)
ODE = os.path.join(gostNetsFolder, "SampleData", "ODE.csv")
ODE = pd.read_csv(ODE)



#%% 
"""
Filter nth nearest

"""

# Check each file to make sure nearest neighbor column is named correctly. If not, rename.
ODE.head(1)
ODE.rename(columns={'Unnamed: 0': 'NN'}, inplace=True)



# Find first nearest POI for each origin node. Run this block for each variable.

ODE["1E"] = 0
Dsub = ODE.iloc[:,1:-1] # Filtering out the newly created field and the node ID column.
ODE["1E"] = Dsub.min(axis=1) # Default is axis=0, meaning min value of each column selected. We want min of each row.
E1 = ODE.loc[:,['NN', '1E']] # Remove unnecessary OD values.
E1.to_csv(os.path.join(pth, '1Et.csv'))


# Find the second nearest POI for each origin node.
fail_value = 999999999
dupes = ODE.apply(pd.Series.duplicated, axis = 1, keep=False) # If a number is repeated within a row, value is True. If not, False.
# The first time this is done, there should be two True values per row, unless any POIs are equidistant.
dupes = ODE.where(~dupes, fail_value) # For any value that appears more than once in its row, it is replaced with the fail_value.

ODE["2E"] = 0
Dsub = dupes.iloc[:,1:] # Filtering out the node ID column. No need to filter 1st nearest as its new "dupes" value is too high to be caught.
ODE["2E"] = Dsub.min(axis=1) 
E2 = ODE.loc[:,['NN', '2E']] 
E2.to_csv(os.path.join(pth, '2Et.csv'))


# Find the third nearest POI for each origin node.
dupes = ODE.apply(pd.Series.duplicated, axis = 1, keep=False)
# Since this includes both first and second nearest columns, there should be four True values per row, unless POIs are equidistant.
dupes = ODE.where(~dupes, fail_value)
 
ODE["3E"] = 0
Dsub = dupes.iloc[:,1:] # Filtering out the node ID column.
ODE["3E"] = Dsub.min(axis=1)
E3 = ODE.loc[:,['NN', '3E']]
E3.to_csv(os.path.join(pth, '3Et.csv'))

# Check that each row shows an increased value from the previous nearest POI.
E1.head(5)
E2.head(5)
E3.head(5)

# Save all scores to one file.
Eall = ODE.loc[:,['NN', '1E', '2E', '3E']]
Eall.to_csv(os.path.join(pth, 'Et.csv'))



#%% 
"""
Create multi-modal travel times by combining walk time to road with drive time to nth nearest service.

"""
#%% If starting new session, re-load from disk.
zwalk = os.path.join(gostNetsFolder, "SampleData", "zwalk.csv") 
zwalk = pd.read_csv(zwalk)
Eall = os.path.join(gostNetsFolder, "SampleData", "Et.csv")
Eall = pd.read_csv(Eall)

#%%
zwalk.head()
Eall.head()
# Merge nearest POIs and walktimes
zwalkE = zwalk.merge(Eall, how='left', left_on='NN', right_on='NN', sort=False)
zwalkE.head()

# Calculate walk time from WorldPop origin to nearest node.
zwalkE["mm1E"] = 0
zwalkE["mm2E"] = 0
zwalkE["mm3E"] = 0
zwalkE["mm1E"] = zwalkE["walk_time"] + zwalkE["1E"]
zwalkE["mm2E"] = zwalkE["walk_time"] + zwalkE["2E"]
zwalkE["mm3E"] = zwalkE["walk_time"] + zwalkE["3E"]


zwalkE.to_csv(os.path.join(pth, 'Etz.csv'))
