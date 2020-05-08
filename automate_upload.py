import arcpy, os, sys
import pandas as pd
from dotenv import load_dotenv
from arcgis import GIS
from arcgis.features import GeoAccessor
from arcgis.features import FeatureLayerCollection
from datetime import date

arcpy.env.overwriteOutput = True

#---------------------------------------------------------------------------
#Inputs
load_dotenv(os.path.join(os.getcwd(), 'environments.env'))
changesGDB = os.getenv('GEOM_CHANGES_DATA')
changes_layer = os.getenv('GEOM_LAYER')
print('GDB source: ' + changesGDB + ' changes fc: ' + changes_layer)
fl_title= changes_layer + '_' + str(date.today())
#---------------------------------------------------------------------------
#Logic

gis = GIS('pro')
print('Logged in as: ' + str(gis.properties.user.username))
# delete old versions if they exist
for item in gis.content.search('title: ' + fl_title):
    item.delete()

geom_changes = pd.DataFrame.spatial.from_featureclass(os.path.join(changesGDB, changes_layer), sr= '3347')
print( 'Uploading feature layer with ' + str(len(geom_changes)) + ' records to AGOL')

geom_fl = geom_changes.spatial.to_featurelayer(
                                    title= fl_title, 
                                    gis= GIS('pro'), 
                                    tags= 'NGD_AL, Redline, ' + str(date.today()))

# Make into a feature layer collection to change properties
geom_flc = FeatureLayerCollection.fromitem(geom_fl)
#Change settings to allow extracts from other users
geom_flc.manager.update_definition({'capabilities':'Query,Extract'})

print('Sharing Layer with NGD')
geom_fl.share( groups= gis.groups.search('title:NGD')[0].groupid)
print('Upload Complete')
