#%% 
import pandana, time, os, pandas as pd, numpy as np
from pandana.loaders import osm
# matplotlib inline
import mpl_toolkits
from mpl_toolkits.basemap import pyproj


#%% Configure script
# configure search at a max distance of 10 km for up to the 10 nearest points-of-interest
# amenities in this case won't be used, since we're pulling from distinct CSV files for each amenity.
amenities = ['pharmacy', 'hospital', 'school']
distance = 10000
num_pois = 10
num_categories = len(amenities) + 1 #one for each amenity, plus one extra for all of them combined

# bounding box as a list of llcrnrlat, llcrnrlng, urcrnrlat, urcrnrlng
bbox = [17.908745, -67.994544, 18.511709, -65.188339] #lat-long bounding box for all islands of Puerto Rico
# For network, ended up not using this and instead specifying each lat/long parameter in network_from_bbox below

#%%
# configure filenames to save/load POI and network datasets
bbox_string = '_'.join([str(x) for x in bbox])
net_filename = 'C:/Users/grace/Documents/Cartography Working Files/data/puerto rico/python codes/demo-puertobbox/prallislands_network_{}.h5'.format(bbox_string)
poi_filename = 'C:/Users/grace/Documents/Cartography Working Files/data/puerto rico/python codes/demo-puertobbox/prallislands_pois_{}_{}.csv'.format('_'.join(amenities), bbox_string)
# This isn't necessary for POIs since they come from CSV.


#%%
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

#%% Download POIs and network data from OSM
start_time = time.time()
if os.path.isfile('pharmacies1.csv'):
    # if a points-of-interest file already exists, just load the dataset from that
    print("in if")
    pois = pd.read_csv('pharmacies1.csv')
    method = 'loaded from CSV'
else:   
    # otherwise, query the OSM API for the specified amenities within the bounding box 
    print("in else")
    osm_tags = '"amenity"~"{}"'.format('|'.join(amenities))
    pois = osm.node_query(bbox[0], bbox[1], bbox[2], bbox[3], tags=osm_tags)
    
    # using the '"amenity"~"school"' returns preschools etc, so drop any that aren't just 'school' then save to CSV
    pois = pois[pois['amenity'].isin(amenities)]
    pois.to_csv(poi_filename, index=False, encoding='utf-8')
    method = 'downloaded from OSM'
    
print('{:,} POIs {} in {:,.2f} seconds'.format(len(pois), method, time.time()-start_time))
pois[['NAME', 'X', 'Y', 'ORGAN_NAME']].head()

# For some reason it printed the X and Y fields as ellipses. 

#%%
# how many pharmacies from each county did we retrieve?
pois['COUNTY'].value_counts()

#%% Next get the street network data - either load an existing dataset 
# for the specified bounding box from HDF5, or get it fresh from the OSM API.

start_time = time.time()
if os.path.isfile('prallislands_network_allnodes.h5'):
    # if a street network file already exists, just load the dataset from that
    print("in if")
    network = pandana.network.Network.from_hdf5('prallislands_network_allnodes.h5')
    method = 'loaded from HDF5'
else:
    print("in else")    
#    # otherwise, query the OSM API for the street network within the specified bounding box
    network = osm.pdna_network_from_bbox(lat_min=17.908745, lng_min=-67.994544, lat_max=18.511709, lng_max=-65.188339)
    method = 'downloaded from OSM'
    
    # identify nodes that are connected to fewer than some threshold of other nodes within a given distance
    lcn = network.low_connectivity_nodes(impedance=10000, count=10, imp_name='distance')
    network.save_hdf5(net_filename, rm_nodes=lcn) #remove low-connectivity nodes and save to h5
   
print('Network with {:,} nodes {} in {:,.2f} secs'.format(len(network.node_ids), method, time.time()-start_time))


#%% Calculate accessibility to any amenity we retrieved
# precomputes the range queries (the reachable nodes within this maximum distance)
# so, as long as you use a smaller distance, cached results will be used
network.precompute(distance + 1)

# This was quick for a 1km distance, timed out for 25km. Took maybe 10 min for 10km.

#%%
# initialize a category for all amenities with the locations specified by the lon and lat columns
network.set_pois(category='all', maxdist=distance, maxitems=num_pois, x_col=pois['X'], y_col=pois['Y'])
# If using OSM data, the x and y column will be 'lon' and 'lat'

#%%
# searches for the n nearest amenities (of all types) to each node in the network
all_access = network.nearest_pois(distance=distance, category='all', num_pois=num_pois)

#%%
all_access.to_csv('pharm_acc_10km.csv', index=True, encoding='utf-8')
# This worked but doesn't georeference the nodes (identified by [id] column).

#%%
# it returned a df with the number of columns equal to the number of POIs that are requested
# each cell represents the network distance from the node to each of the n POIs
print('{:,} nodes'.format(len(all_access)))
all_access.head()


#%% Plot accessibility from each node to any amenity

# distance to the nearest amenity of any type
n = 1
bmap, fig, ax = network.plot(all_access[n], bbox=bbox, plot_kwargs=plot_kwargs, fig_kwargs=fig_kwargs, 
                             bmap_kwargs=bmap_kwargs, cbar_kwargs=cbar_kwargs)
ax.set_facecolor(bgcolor)
ax.set_title('Road distance (m) to nearest pharmacy in Puerto Rico', fontsize=15)
fig.savefig('10km/accessibility-pharm-pr.png', dpi=200, bbox_inches='tight')


#%%
# distance to the 5th nearest amenity of any type
n = 5
bmap, fig, ax = network.plot(all_access[n], bbox=bbox, plot_kwargs=plot_kwargs, fig_kwargs=fig_kwargs, 
                             bmap_kwargs=bmap_kwargs, cbar_kwargs=cbar_kwargs)
ax.set_facecolor(bgcolor)
ax.set_title('Road distance (m) to 5th nearest pharmacy in Puerto Rico', fontsize=15)
fig.savefig('10km/accessibility-5-pharm-pr.png', dpi=200, bbox_inches='tight')

#%%
# distance to the nearest amenity of any type, as hexbins
bmap, fig, ax = network.plot(all_access[1], bbox=bbox, plot_type='hexbin', plot_kwargs=hex_plot_kwargs, 
                             fig_kwargs=fig_kwargs, bmap_kwargs=bmap_kwargs, cbar_kwargs=cbar_kwargs)
ax.set_facecolor(bgcolor)
ax.set_title('Road distance (m) to nearest pharmacy in Puerto Rico', fontsize=15)
fig.savefig('10km/accessibility-hex-pharm-pr.png', dpi=200, bbox_inches='tight')



"""
Below is useful if I put pharmacies, urgent care, and hospitals into one csv file.
If I do this, need to change the amenity types specified in Configure Script code block (line 28).
"""
#%% 5. Calculate and plot accessibility separately for each amenity type
# The amenity types specified at the beginning area: restaurants, bars, and schools

# initialize each amenity category with the locations specified by the lon and lat columns
for amenity in amenities:
    pois_subset = pois[pois['amenity']==amenity]
    network.set_pois(category=amenity, maxdist=distance, maxitems=num_pois, x_col=pois_subset['lon'], y_col=pois_subset['lat'])

# Remember to add maxdist and maxitems parameters to set_pois function
    
#%%
    # distance to the nearest restaurant
restaurant_access = network.nearest_pois(distance=distance, category='restaurant', num_pois=num_pois)
bmap, fig, ax = network.plot(restaurant_access[1], bbox=bbox, plot_kwargs=plot_kwargs, 
                             fig_kwargs=fig_kwargs, bmap_kwargs=bmap_kwargs, cbar_kwargs=cbar_kwargs)
ax.set_facecolor(bgcolor)
ax.set_title('Walking distance (m) to nearest restaurant around Puerto Rico', fontsize=15)
fig.savefig('C:/Users/grace/Documents/Cartography Working Files/data/puerto rico/python codes/puertopython/accessibility-restaurant-pr.png', dpi=200, bbox_inches='tight')

#%%
# distance to the nearest bar
bar_access = network.nearest_pois(distance=distance, category='bar', num_pois=num_pois)
bmap, fig, ax = network.plot(bar_access[1], bbox=bbox, plot_kwargs=plot_kwargs, 
                             fig_kwargs=fig_kwargs, bmap_kwargs=bmap_kwargs, cbar_kwargs=cbar_kwargs)
ax.set_facecolor(bgcolor)
ax.set_title('Walking distance (m) to nearest bar around Puerto Rico', fontsize=15)
fig.savefig('C:/Users/grace/Documents/Cartography Working Files/data/puerto rico/python codes/puertopython/accessibility-bar-pr.png', dpi=200, bbox_inches='tight')


#%%
# distance to the nearest school
school_access = network.nearest_pois(distance=distance, category='school', num_pois=num_pois)
bmap, fig, ax = network.plot(school_access[1], bbox=bbox, plot_kwargs=plot_kwargs, 
                             fig_kwargs=fig_kwargs, bmap_kwargs=bmap_kwargs, cbar_kwargs=cbar_kwargs)
ax.set_facecolor(bgcolor)
ax.set_title('Walking distance (m) to nearest school around Puerto Rico', fontsize=15)
fig.savefig('C:/Users/grace/Documents/Cartography Working Files/data/puerto rico/python codes/puertopython/accessibility-school-pr.png', dpi=200, bbox_inches='tight')

