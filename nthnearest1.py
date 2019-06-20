# -*- coding: utf-8 -*-
"""
How to subset the nearest point of interest from an Origin-Destination matrix,
as well as the 2nd, 3rd, or "nth" nearest.

"""
#%%
"""
Configure script.

"""
# Note: gostnet.py is in the working directory folder.
import os, sys
gostNetsFolder = os.path.dirname(os.getcwd())
sys.path.insert(0, gostNetsFolder)
import pandas as pd

pth = os.path.join(gostNetsFolder, "SampleData")


#%%  Re-load from disk.

OD = os.path.join(gostNetsFolder, "SampleData", "OD.csv")
OD = pd.read_csv(OD)


# Check each file to make sure nearest neighbor column is named correctly. If not, rename.
# Nearest neighbor ID will serve as the index.
OD.head(1)
OD.rename(columns={'Unnamed: 0': 'NN'}, inplace=True)


#%% Nth nearest POI
fail_value = 999999999

# Find first nearest POI for each origin node.

OD["1D"] = 0
ODsub = OD.iloc[:,1:44] # Subset only the POI columns. Remove NN and 1D fields.
# I chose to select on the columns I wanted instead of excepting those I didn't because I've noticed issues
# where index columns are doubled upon loading the csv with Pandas. Being very deliberate here.
OD["1D"] = ODsub.min(axis=1) # Default is axis=0, meaning min value of each column selected. We want min of each row.
OD.head(1) # Check that it worked. 1D column should contain the smallest number from each row.
OD1 = OD.loc[:,['NN', '1D']] # Remove unnecessary OD values.
OD1.to_csv(os.path.join(pth, '1D.csv'))



# Find the second nearest POI for each origin node.
dupes = OD.apply(pd.Series.duplicated, axis = 1, keep=False)
# The first time this is done, there should be two True values per row.
dupes = OD.where(~dupes, fail_value) # For any value that appears more than once in its row, it is replaced with the fail_value.

OD["2D"] = 0
ODsub = dupes.iloc[:,1:44]
OD["2D"] = ODsub.min(axis=1) # Now that we're selecting from the dupes dataframe, this will ignore the 1st lowest values in each row.
OD.head(1)
OD2 = OD.loc[:,['NN', '2D']] 
OD2.to_csv(os.path.join(pth, '2D.csv'))


# Find the third nearest POI for each origin node.
dupes = OD.apply(pd.Series.duplicated, axis = 1, keep=False)
# Since this includes both columns 1D and 2D, there should be four True values per row.
dupes = OD.where(~dupes, fail_value)

OD["3D"] = 0
ODsub = dupes.iloc[:,1:44]
OD["3D"] = ODsub.min(axis=1)
OD.head(1)
OD3 = OD.loc[:,['NN', '3D']]
OD3.to_csv(os.path.join(pth, '3D.csv'))


# Save all scores to one file.
ODall = OD.loc[:,['NN', '1D', '2D', '3D']]
ODall.to_csv(os.path.join(pth, '123D.csv'))



