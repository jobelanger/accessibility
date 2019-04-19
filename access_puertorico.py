# -*- coding: utf-8 -*-
"""
Only the final workflow here.

"""

#%% 
"""
Configure script.

"""
import pandana, time, os, pandas as pd, numpy as np
from pandana.loaders import osm
# matplotlib inline
import mpl_toolkits
from mpl_toolkits.basemap import pyproj
import networkx as nx

#%% 
# configure search at a max distance of 1 km for up to the 10 nearest points-of-interest
distance = 40000
num_pois = 5

# bounding box as a list of llcrnrlat, llcrnrlng, urcrnrlat, urcrnrlng
bbox = [17.908745, -67.994544, 18.511709, -65.188339] #lat-long bounding box for all islands of Puerto Rico
# For network, ended up not using this and instead specifying each lat/long parameter in network_from_bbox below

#%% 
"""
Import data from disk.

"""

start_time = time.time()
pois = pd.read_csv('dialysis2.csv')
method = 'loaded from CSV'

    
print('{:,} POIs {} in {:,.2f} seconds'.format(len(pois), method, time.time()-start_time))
pois[['Facility Name', 'City', 'long', 'lat']].head(10)


#%%
# how many amenities from each county did we retrieve?
pois['County'].value_counts()

#%% Next get the street network data

start_time = time.time()

network = pandana.network.Network.from_hdf5('prallislands_network_allnodes.h5')
method = 'loaded from HDF5'

print('Network with {:,} nodes {} in {:,.2f} secs'.format(len(network.node_ids), method, time.time()-start_time))


#%% 

"""
Calculate accessibility to any amenity we retrieved

"""

# precomputes the range queries (the reachable nodes within this maximum distance)
# so, as long as you use a smaller distance, cached results will be used
network.precompute(distance + 1)

#%%
# initialize a category for all amenities with the locations specified by the lon and lat columns
network.set_pois(category='all', maxdist=distance, maxitems=num_pois, x_col=pois['long'], y_col=pois['lat'])

#%%
# searches for the n nearest amenities (of all types) to each node in the network
dialysis_access = network.nearest_pois(distance=distance, category='all', num_pois=num_pois)

#%%
network2_gdf = network.nodes_df
print(network2_gdf.shape, dialysis_access.shape)

#%%
network2_gdf.to_csv('40km/allnodes_1stk12_40km.csv', index=True, encoding='utf-8')

#%%
dialysis_access.to_csv('40km/dial_acc_40km.csv', index=True, encoding='utf-8')
# This doesn't georeference the nodes (identified by [id] column).
# Georeference by joining network nodes file and amenity file in QGIS.

#%%
"""
Next steps are in QGIS:
    Add network nodes csv and save as shapefile
    Join amenity csv to network nodes shapefile
    Relate network nodes shapefile to population data
    Average to municipality
"""


#%%
"""
Visualizing results.

"""
# keyword arguments to pass for the matplotlib figure
bbox_aspect_ratio = (bbox[2] - bbox[0]) / (bbox[3] - bbox[1])
fig_kwargs = {'facecolor':'w', 
              'figsize':(10, 10 * bbox_aspect_ratio)}

# keyword arguments to pass for scatter plots
plot_kwargs = {'s':5, 
               'alpha':0.9, 
               'cmap':'viridis_r', 
               'edgecolor':'none'}

# network aggregation plots are the same as regular scatter plots, but without a reversed colormap
agg_plot_kwargs = plot_kwargs.copy()
agg_plot_kwargs['cmap'] = 'viridis'

# keyword arguments to pass for hex bin plots
hex_plot_kwargs = {'gridsize':60,
                   'alpha':0.9, 
                   'cmap':'viridis_r', 
                   'edgecolor':'none'}

# keyword arguments to pass to make the colorbar
cbar_kwargs = {}

# keyword arguments to pass to basemap
bmap_kwargs = {}

# color to make the background of the axis
bgcolor = 'k'

#%% Plot accessibility from each node to any amenity

# distance to the nearest amenity of any type
n = 1
bmap, fig, ax = network.plot(dialysis_access[n], bbox=bbox, plot_kwargs=plot_kwargs, fig_kwargs=fig_kwargs, 
                             bmap_kwargs=bmap_kwargs, cbar_kwargs=cbar_kwargs)
ax.set_facecolor(bgcolor)
ax.set_title('Road distance (m) to nearest dialysis service in Puerto Rico', fontsize=15)
fig.savefig('40km/accessibility-dial-pr.png', dpi=200, bbox_inches='tight')


#%% 
# distance to the 5th nearest amenity of any type
n = 3
bmap, fig, ax = network.plot(dialysis_access[n], bbox=bbox, plot_kwargs=plot_kwargs, fig_kwargs=fig_kwargs, 
                             bmap_kwargs=bmap_kwargs, cbar_kwargs=cbar_kwargs)
ax.set_facecolor(bgcolor)
ax.set_title('Road distance (m) to 3rd nearest dialysis service in Puerto Rico', fontsize=15)
fig.savefig('40km/accessibility-3-dial-pr.png', dpi=200, bbox_inches='tight')

