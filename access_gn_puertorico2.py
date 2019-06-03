# -*- coding: utf-8 -*-
"""
GOSTNets workflow for network analysis in Puerto Rico.
Primarily based off of the sample notebooks provided by GOSTNets creator Charles Fox: https://github.com/Charlesfox1/GOSTnets

Document created 28 May 2019.
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
from shapely.geometry import Point
import fiona
import peartree
import geopandas as gpd
import osmnx as ox
import networkx as nx

pth = os.path.join(gostNetsFolder, "SampleData")

#%% 
"""
Load the data.

"""
# Multi-point shapefiles don't read well. Re-created shapefile from csv with geopandas for each offending file.
dfH = os.path.join(gostNetsFolder, "SampleData", "hospitals1.csv")
dfH = pd.read_csv(dfH)
geometry = [Point(xy) for xy in zip(dfH.X, dfH.Y)]
crs = {'init': 'epsg:4326'} 
gdfH = GeoDataFrame(dfH, crs=crs, geometry=geometry)
gdfH.to_file(driver='ESRI Shapefile', filename='hospitals2.shp') 

dfD = os.path.join(gostNetsFolder, "SampleData", "dialysis2.csv")
dfD = pd.read_csv(dfD)
geometry = [Point(xy) for xy in zip(dfD.long, dfD.lat)]
crs = {'init': 'epsg:4326'} 
gdfD = GeoDataFrame(dfD, crs=crs, geometry=geometry)
gdfD.to_file(driver='ESRI Shapefile', filename='dialysis2wgs84.shp') 

dfG = os.path.join(gostNetsFolder, "SampleData", "gas3.csv")
dfG = pd.read_csv(dfG)
geometry = [Point(xy) for xy in zip(dfG.X, dfG.Y)]
crs = {'init': 'epsg:4326'} 
gdfG = GeoDataFrame(dfG, crs=crs, geometry=geometry)
gdfG.to_file(driver='ESRI Shapefile', filename='gas4wgs84.shp') 

dfE = os.path.join(gostNetsFolder, "SampleData", "education3.csv")
dfE = pd.read_csv(dfE)
geometry = [Point(xy) for xy in zip(dfE.X, dfE.Y)]
crs = {'init': 'epsg:4326'} 
gdfE = GeoDataFrame(dfE, crs=crs, geometry=geometry)
gdfE.to_file(driver='ESRI Shapefile', filename='education3wgs84.shp') 
# Make sure each file is in WGS84, the same CRS as OpenStreetMap data.
# Note, this saves to the working directory.

aoi = r'prboundingwgs84.shp' 
# Graph didn't populate on the smaller islands when using the Puerto Rico admin boundary.
# Created a rectangular bounding box (in QGIS) to use as the AOI instead.
inputOrigins = os.path.join(gostNetsFolder, "SampleData", "wpop2wgs84.shp")
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

# Generate shape from shapefile
shp = gpd.read_file(os.path.join(pth, aoi))
bound = shp.geometry.iloc[0]
bound
#%% 
""" 
Get driving network for all islands in Puerto Rico. 

"""

gDrive = ox.graph_from_polygon(bound, network_type= 'drive')
# This took about half an hour.
# Note: length is measured in meters.

#%% 
"""
Observe network and save to file.

"""

gn.example_edge(gDrive, 2)

# Create separate variables for edges (line) of network and nodes (point).
gDrive_edge_gdf = gn.edge_gdf_from_graph(gDrive)
gDrive_node_gdf = gn.node_gdf_from_graph(gDrive)


# Summary of roads broken down by highway type. Replacing multiple answers with first listed type.
def check(x):
    if type(x.highway) == list:
        return x.highway[0]
    else:
        return x.highway
gDrive_edge_gdf['highway'] = gDrive_edge_gdf.apply(lambda x: check(x), axis = 1)

len(gDrive_edge_gdf) # 392001 edges
gDrive_edge_gdf.highway.value_counts() # Most are residential, tertiary, secondary, and unclassified.

print('number of roads in object: %d' % gDrive.number_of_edges())
print('number of nodes in object: %d' % gDrive.number_of_nodes())

# Save graph edges and nodes to file as csv.
gDrive_edge_gdf.to_csv(os.path.join(pth, 'drive_dist_edge.csv'))
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
gDriveTime = gn.convert_network_to_time(gDrive, distance_tag = 'length', graph_type = networkType, speed_dict = speed_dict)
# Note: time is in seconds.

#%% 
"""
Observe network and save to file.

"""

gn.example_edge(gDriveTime, 2)

gDriveTime_edge_gdf = gn.edge_gdf_from_graph(gDriveTime)
gDriveTime_node_gdf = gn.node_gdf_from_graph(gDriveTime)
gDriveTime_edge_gdf['highway'] = gDriveTime_edge_gdf.apply(lambda x: check(x), axis = 1)

len(gDriveTime_edge_gdf) # 392001 edges (should be same as gWalk)
gDriveTime_edge_gdf.highway.value_counts()


gDriveTime_edge_gdf.to_csv(os.path.join(pth, 'drive_time_edge.csv'))
gDriveTime_node_gdf.to_csv(os.path.join(pth, 'drive_time_node.csv'))

#%%
"""
Origins and destinations

"""

#%% 
""" 
Measure distance from origin/destination to nearest node and save to file.

"""

inOsnap = gn.pandana_snap(gDrive, inO, add_dist_to_node_col = True)
# Took maybe 20 min
inOsnap.to_csv('inOsnap.csv', index=True)

inDsnap = gn.pandana_snap(gDrive, inD, add_dist_to_node_col = True)
inDsnap.to_csv('inDsnap.csv', index=True)
inHsnap = gn.pandana_snap(gDrive, inH, add_dist_to_node_col = True)
inHsnap.to_csv('inHsnap.csv', index=True)
inGsnap = gn.pandana_snap(gDrive, inG, add_dist_to_node_col = True)
inGsnap.to_csv('inGsnap.csv', index=True)
inPsnap = gn.pandana_snap(gDrive, inP, add_dist_to_node_col = True)
inPsnap.to_csv('inPsnap.csv', index=True)
inEsnap = gn.pandana_snap(gDrive, inE, add_dist_to_node_col = True)
inEsnap.to_csv('inEsnap.csv', index=True)


#"""
#If already created, load from file.
#
#Note: this didn't work. Investigate read_file geometry type.
#
#"""
#
#inOsnap = os.path.join(gostNetsFolder, "SampleData", "inOsnap.csv")
#inOsnap = gpd.read_file(inOsnap)

#%% 
""" 
Remove duplicates of nearest nodes for origins and destinations 

Note: This is useful for measuring the distance from origin["NN"] to destination["NN"] but 
it removes the possibility for measuring origin to NN and NN to destination.
That needs to be done through a (population-weighted) average on the original inXsnap.

"""

# Method which maintains the gdf format:
# convert to wkb
inDsnap["geometry"] = inDsnap["geometry"].apply(lambda geom: geom.wkb)
inDsnapunique = inDsnap.drop_duplicates(["NN"])
# convert back to shapely geometry
inDsnapunique["geometry"] = inDsnapunique["geometry"].apply(lambda geom: shapely.wkb.loads(geom))
inDsnapunique = inDsnapunique.copy()

inOsnapunique = inOsnap.copy()
inOsnapunique["geometry"] = inOsnapunique["geometry"].apply(lambda geom: geom.wkb)
inOsnapunique = inOsnapunique.drop_duplicates(["NN"])
# convert back to shapely geometry
inOsnapunique["geometry"] = inOsnapunique["geometry"].apply(lambda geom: shapely.wkb.loads(geom))
# 141,791 rows

inHsnapunique = inHsnap.copy()
inHsnapunique["geometry"] = inHsnapunique["geometry"].apply(lambda geom: geom.wkb)
inHsnapunique = inHsnapunique.drop_duplicates(["NN"])

# convert back to shapely geometry
inHsnapunique["geometry"] = inHsnapunique["geometry"].apply(lambda geom: shapely.wkb.loads(geom))
# 69 rows

inGsnapunique = inGsnap.copy()
inGsnapunique["geometry"] = inGsnapunique["geometry"].apply(lambda geom: geom.wkb)
inGsnapunique = inGsnapunique.drop_duplicates(["NN"])
# convert back to shapely geometry
inGsnapunique["geometry"] = inGsnapunique["geometry"].apply(lambda geom: shapely.wkb.loads(geom))
# 316 rows

inPsnapunique = inPsnap.copy()
inPsnapunique["geometry"] = inPsnapunique["geometry"].apply(lambda geom: geom.wkb)
inPsnapunique = inPsnapunique.drop_duplicates(["NN"])
# convert back to shapely geometry
inPsnapunique["geometry"] = inPsnapunique["geometry"].apply(lambda geom: shapely.wkb.loads(geom))
# 926 rows

inEsnapunique = inEsnap.copy()
inEsnapunique["geometry"] = inEsnapunique["geometry"].apply(lambda geom: geom.wkb)
inEsnapunique = inEsnapunique.drop_duplicates(["NN"])
# convert back to shapely geometry
inEsnapunique["geometry"] = inEsnapunique["geometry"].apply(lambda geom: shapely.wkb.loads(geom))
# 1426 rows



# Method which depends on pandas df and conversion back to gdf.
inOsnapdf = pd.DataFrame(inOsnap)
duplist = inOsnapdf.duplicated('NN')
inOsnapdf = inOsnapdf.drop_duplicates(['NN'])
inOsnapdf[["NN", "drivetimeD", "drivetimeH", "drivetimeG", "drivetimeP", 
           "drivetimeE"]] = inOsnapdf[["NN", "drivetimeD", "drivetimeH", 
                        "drivetimeG", "drivetimeP", "drivetimeE"]].apply(pd.to_numeric)
inOsnapdfunique2 = gpd.GeoDataFrame(
    inOsnapdf, geometry='geometry')

inHsnapdf = pd.DataFrame(inHsnap)
duplist = inHsnapdf.duplicated('NN')
inHsnapdf = inHsnapdf.drop_duplicates(['NN'])
inHsnapdf[["NN"]] = inHsnapdf[["NN"]].apply(pd.to_numeric)
inHsnapdfunique = gpd.GeoDataFrame(
    inHsnapdf, geometry='geometry')


#%% 
"""
Create origin-destination accessibility scores for all nearest nodes.

"""


#%%
inOsnapunique.head(3)

inOsnapunique['drivetimeD'] = 0
inOsnapunique['drivetimeH'] = 0
inOsnapunique['drivetimeG'] = 0
inOsnapunique['drivetimeP'] = 0
inOsnapunique['drivetimeE'] = 0

inOsnap['drivetimeD'] = 0
inOsnap['drivetimeH'] = 0
inOsnap['drivetimeG'] = 0
inOsnap['drivetimeP'] = 0
inOsnap['drivetimeE'] = 0


for i in range(0, len(inOsnapunique)):
    try:
        origin = inOsnapunique.NN.loc[i]
        destination = inDsnapunique.NN.loc[i] 
        inOsnapunique['drivetimeD'].loc[i] = nx.shortest_path_length(gDriveTime, source=origin, target=destination, weight='time')
    except:
        inOsnapunique['drivetimeD'].loc[i] = None
    if i % 100 == 0 and i != 0:
        print('%d trips done' % i)
    elif i == len(inOsnapunique):
        print('Analysis complete')
# Started sometime around 7:20 or later. 18,000 trips complete by 7:40. Estimated at 2.5 hours runtime.
# This only worked for the first 5 rows...
# Trying variations on except clause. Usual code stopped after first row. Exception: pass stopped after 5th row.

inOsnapunique.to_csv(os.path.join(pth, 'access_drivetime_sec_nn.csv'))

# Convert from seconds to minutes
out = inOsnapunique.copy()
out['drivetimeD'] = out['drivetimeD'] / 60
out.to_csv(os.path.join(pth, 'access_drivetime_nn.csv'))


#%% Using gn.calculate_OD instead of nx.shortest_path_length
fail_value = 999999999
accDriveTime = gn.calculate_OD(gDriveTime, list(inOsnapdfunique2.NN), list(inHsnapunique.NN), fail_value, weight = 'time')
accDriveMin = accDriveTime[accDriveTime < fail_value] / 60
pd.Series(accDriveMin.ravel()).shape

pd.Series(accDriveMin).describe()
accDriveMin_df = pd.DataFrame(accDriveMin)

accDriveTime2 = pd.DataFrame

# I understand making the OD matrix but can't find a way to assign the drive times back onto the nodes.

