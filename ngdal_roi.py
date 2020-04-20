# Compare the redline NGD_AL data against the source data to detect changes

import geopandas as gpd

# paths
redline_path = '../redline_ngdal.geojson'

ngd_db_path = '../ngd_national.gdb'
ngdal_layer = 'WC2021NGD_AL_20200313'

# read the redline data and get a list of attributes that have changed
print("Reading redline data")
rdf = gpd.read_file(redline_path)
# make a list of the NGD_UIDs that have changed so that we can filter the NGD_AL later
# null will end up in this list, but that won't hurt later
modified_ngduids = rdf['NGD_UID'].unique().tolist()

# read the NGD_AL source data, but only keep records that are in the redline layer
print("Reading NGD_AL")
ngdal = gpd.read_file(ngd_db_path, layer=ngdal_layer)
print("Filtering NGD_AL to only modified records")
ngdal = ngdal.loc[ngdal['NGD_UID'].isin(modified_ngduids)]

# write out the NGD_AL records that have an entry in the redline data
print("Writing records that have a correlated redline entry")
ngdal.to_file("../ngdal_affected.geojson", driver='GeoJSON')