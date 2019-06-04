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

#%%
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
gn.save(gDrive, 'gDrive', '', edges = False, nodes = False)

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



#%% Save graph as gn.save
# Saves as a pickle

gn.save(gDriveTime, 'PR_graph', '', edges = False, nodes = False)

# Reload graph from file
gDriveTime = nx.read_gpickle("gDrive.pickle")
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


"""
If already created, load from file.

"""

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
#""" 
#Remove duplicates of nearest nodes for origins and destinations 
#
#"""
# Method which maintains the gdf format:
#from shapely.wkt import loads
#
#inOsnapunique = inOsnap.copy()
#inOsnapunique["geometry"] = inOsnapunique["geometry"].apply(loads)
## convert back to shapely geometry
## 141,791 rows


#%% 
"""
Create origin-destination accessibility scores for all nearest nodes.

"""

# Using calculate_OD
fail_value = 999999999
origins = list(inOsnap.NN.unique())
listD = list(inDsnap.NN.unique()) 
listH = list(inHsnap.NN.unique()) 
listG = list(inGsnap.NN.unique()) 
listP = list(inPsnap.NN.unique()) 
listE = list(inEsnap.NN.unique())
destslist = listD + listH + listG + listP + listE
dests = list(set(destslist))
len(dests)
# calculate_OD TypeError: 'set' object does not support indexing. Made the set a list and it worked.


accDriveTime = gn.calculate_OD(gDriveTime, origins, dests, fail_value, weight = 'time')
# Full 5 variable list (destslist) started sometime around 1pm. Finished at 2:45pm.

# Since memory error was happening with saving accDriveTime (on June 3), need to re-do calculate_OD. 
# But since D, H, and G subsets saved normally, we can use calculate_OD on only the P and E files.
accDriveTimeP = gn.calculate_OD(gDriveTime, origins, listP, fail_value, weight = 'time')
accDriveTimeE = gn.calculate_OD(gDriveTime, origins, listE, fail_value, weight = 'time')
# Pharmacies started at 10:06am, ended 10:39am
# Education started 1:05pm, ended before 2pm.

#%% Convert to minutes and save to file.
accDriveTimedf = pd.DataFrame(accDriveTime, index = origins, columns = dests)
accDriveTimedf.head(5)
accDriveTimedf.to_csv(os.path.join(pth, 'accDriveTime.csv'))
# Attempted to write to csv. Errno28 no space left on device.
accDriveMin = accDriveTimedf[accDriveTimedf <fail_value] / 60
# Memory Error.

# Create POI-specific OD and save to file.
accDriveTimeD = accDriveTimedf.loc[:, listD]
accDriveTimeD.to_csv(os.path.join(pth, 'accDriveTimeD.csv'))
accDriveTimeH = accDriveTimedf.loc[:, listH]
accDriveTimeH.to_csv(os.path.join(pth, 'accDriveTimeH.csv'))
accDriveTimeG = accDriveTimedf.loc[:, listG]
accDriveTimeG.to_csv(os.path.join(pth, 'accDriveTimeG.csv'))
# Pharmacies and Education are giving me memory errors. They are 926 and 1426 values respectively.
accPdf = pd.DataFrame(accDriveTimeP, index = origins, columns = listP)
accPdf.to_csv(os.path.join(pth, 'accDriveTimeP.csv')) # Started 10:40am, completed successfully 10:44am.
accEdf = pd.DataFrame(accDriveTimeE, index = origins, columns = listE)
accEdf.to_csv(os.path.join(pth, 'accDriveTimeE.csv')) # Successful.
# If memory error continues, then halve the accXdf datasets first.


# Convert time to minutes and save to file.
accDmin = accDriveTimeD[accDriveTimeD < fail_value] / 60
accDmin.to_csv(os.path.join(pth, 'accDmin.csv'))
accHmin = accDriveTimeH[accDriveTimeH < fail_value] / 60
accHmin.to_csv(os.path.join(pth, 'accHmin.csv'))
accGmin = accDriveTimeG[accDriveTimeG < fail_value] / 60
accGmin.to_csv(os.path.join(pth, 'accGmin.csv'))
# Waiting to resolve memory error above before doing P and E.
# Resolved.
accPmin = accPdf[accPdf <fail_value] / 60 
accPmin.to_csv(os.path.join(pth, 'accPmin.csv')) # Started 2:31pm. Done by 2:38pm.
accEmin = accEdf[accEdf <fail_value] / 60
accEmin.to_csv(os.path.join(pth, 'accEmin.csv'))

#%% Re-load from disk.

accDmin = os.path.join(gostNetsFolder, "SampleData", "accDmin.csv")
accDmin = pd.read_csv(accDmin)
accHmin = os.path.join(gostNetsFolder, "SampleData", "accHmin.csv")
accHmin = pd.read_csv(accHmin)
accGmin = os.path.join(gostNetsFolder, "SampleData", "accGmin.csv")
accGmin = pd.read_csv(accGmin)
accPmin = os.path.join(gostNetsFolder, "SampleData", "accPmin.csv")
accPmin = pd.read_csv(accPmin)
accEmin = os.path.join(gostNetsFolder, "SampleData", "accEmin.csv")
accEmin = pd.read_csv(accEmin)
accGmin.head(10)
accPmin.head(10)


#%%
# Find first nearest POI for each origin node.
accDmin["1D"] = 0
accDsubset = accDmin.iloc[:,1:44]
accDmin["1D"] = accDsubset.min(axis=1) # Default is axis=0, meaning min value of each column selected. We want min of each row.
accDmin.head(1)
accDmin.rename(columns={'Unnamed: 0': 'NN'}, inplace=True)
accDmin2 = accDmin.loc[:,['NN', '1D']] # Remove unnecessary OD values.
accDmin2.to_csv(os.path.join(pth, 'accD.csv'))

accHsub = accHmin.iloc[:, 1:70] # Avoid selection of NN ID as the minimum time.
accHmin["1H"] = 0
accHmin["1H"] = accHsub.min(axis=1)
accHmin.head(1)
accHmin.rename(columns={'Unnamed: 0': 'NN'}, inplace=True)
accH = accHmin.loc[:,['NN', '1H']] # Remove unnecessary OD values.
accH.to_csv(os.path.join(pth, 'accH.csv'))


accGsub = accGmin.iloc[:, 1:317] # Avoid selection of NN ID as the minimum time.
accGmin["1G"] = 0
accGmin["1G"] = accGsub.min(axis=1)
accGmin.head(1)
accGmin.rename(columns={'Unnamed: 0': 'NN'}, inplace=True)
accG = accGmin.loc[:,['NN', '1G']] # Remove unnecessary OD values.
accG.to_csv(os.path.join(pth, 'accG.csv'))


accPsub = accPmin.iloc[:, 1:927] # Avoid selection of NN ID as the minimum time.
accPmin["1P"] = 0
accP1half = accPmin.iloc[:70000, :]
accP1halfsub = accPsub.iloc[:70000, :]
accP1half["1P"] = accP1halfsub.min(axis=1)

accPmin.rename(columns={'Unnamed: 0': 'NN'}, inplace=True)
accP = accPmin.loc[:,['NN', '1P']] # Remove unnecessary OD values.




accEsub = accEmin.iloc[:, 1:1427] # Avoid selection of NN ID as the minimum time.
accEmin["1E"] = 0
accEmin["1E"] = accEsub.min(axis=1)
accEmin.head(1)
accEmin.rename(columns={'Unnamed: 0': 'NN'}, inplace=True)
accE = accEmin.loc[:,['NN', '1E']] # Remove unnecessary OD values.
accEsub.head(1)

# Find the second closest dialysis center.
# Still developing this code.
#accDmin["2D"] = 0
#accDsubset2 = accDmin.iloc[:,1:44]
#smallestD = accDsubset2.min(axis=1)
#for i, c in range(0, len(accDsubset2)):
#    if i is accDsubset2[c].min()
#        i == 0
#accDsubset2.head()
#accDmin["2D"] = accDsubset2.min(axis=1)


#%% Load from disk
accD = os.path.join(gostNetsFolder, "SampleData", "accD.csv")
accD = pd.read_csv(accD)
accH = os.path.join(gostNetsFolder, "SampleData", "accH.csv")
accH = pd.read_csv(accH)
accG = os.path.join(gostNetsFolder, "SampleData", "accG.csv")
accG = pd.read_csv(accG)
accP = os.path.join(gostNetsFolder, "SampleData", "accP.csv")
accP = pd.read_csv(accP)
accE = os.path.join(gostNetsFolder, "SampleData", "accE.csv")
accE = pd.read_csv(accE)
accG.head(10)
accP.head(10)
accE.head(10)


# Merge nearest POIs and walktimes
inOsnapD = inOsnap.merge(accD, how='left', left_on='NN', right_on='NN', sort=False)
inOsnapD.head(3)
inOsnapDH = inOsnapD.merge(accH, how='left', left_on='NN', right_on='NN', sort=False)
inOsnapDH.head(3)
inOsnapDHG = inOsnapDH.merge(accG, how='left', left_on='NN', right_on='NN', sort=False)
inOsnapDHG.head(3)

# Calculate walk time from WorldPop origin to nearest node.
inOsnapDHG.head(10)
inOsnapDHG["walktime"] = 0
inOsnapDHG["walktime"] = inOsnapDHG["NN_dist"] / 75 # Walking at 75 meters per minute (4.5 km per hour)
# Walk times range from only 0-16 seconds. 

# Since walk times to the nearest road are so short, this calculation isn't necessary.
#list(inOsnapDHG)
#inOsnapDHG["mmtimeD"] = 0
#inOsnapDHG["mmtimeH"] = 0
#inOsnapDHG["mmtimeG"] = 0
#for node in range(0, len(inOsnapDHG)):
#    inOsnapDHG["mmtimeD"] = inOsnapDHG["walktime"] + inOsnapDHG["1D"]
#    inOsnapDHG["mmtimeH"] = inOsnapDHG["walktime"] + inOsnapDHG["1H"]
#    inOsnapDHG["mmtimeG"] = inOsnapDHG["walktime"] + inOsnapDHG["1G"]    
#    if node % 300 == 0 and node != 0:
#        print('%d trips done' % node)
#    elif node == len(inOsnapDHG):
#        print('Analysis complete')
# Started at 4:42pm. Runs about 240 calculations per minute. Estimated completion: 225 hours??
# Cut it short due to ineffectual influence on municipal ratings.
inOsnapDHG.head(2)


#%%
"""
Next steps: 
    1. try operating & saving & subsetting the calculate_OD with as few variables loaded as possible
        i. does this solve the weird short distance issue with pharmacies and education?
    2. figure out the short distance issue with pharmacies and education.
    4. DONE. create pop-weighted average municipal scores from drive time.
    6. prepare data for statistical modeling.
    5. elevation impedance

"""

