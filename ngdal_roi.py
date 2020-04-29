# Compare the redline NGD_AL data against the source data to extract only records of interest for change detection

import geopandas as gpd
from dotenv import load_dotenv
import os

# load environment to get settings
load_dotenv()

# paths
redline_path = os.getenv('NGD_REDLINE_DATA')

ngd_db_path = os.getenv('NGD_NGDAL_DATA')
ngdal_layer = os.getenv('NGD_NGDAL_LAYER')
ngdal_affected_path = os.getenv('NGD_NGDAL_AFFECTED_FILE')

uid_field = os.getenv('NGD_UID_FIELD')

# read the redline data and get a list of attributes that have changed
print("Reading redline data")
rdf = gpd.read_file(redline_path)
# make a list of the NGD_UIDs that have changed so that we can filter the NGD_AL later
# null will end up in this list, but that won't hurt later
modified_ngduids = rdf[uid_field].unique().tolist()

# read the NGD_AL source data, but only keep records that are in the redline layer
print("Reading NGD_AL")
ngdal = gpd.read_file(ngd_db_path, layer=ngdal_layer)
print("Filtering NGD_AL to only modified records")
ngdal = ngdal.loc[ngdal[uid_field].isin(modified_ngduids)]

# write out the NGD_AL records that have an entry in the redline data
print("Writing records that have a correlated redline entry")
ngdal.to_file(ngdal_affected_path, driver='GeoJSON')