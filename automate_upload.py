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

CSD_data = os.path.join(os.getcwd(), 'CSD_202009.gdb', 'WC2021CSD_202009')

print('GDB source: ' + changesGDB + ' changes fc: ' + changes_layer)
fl_title= changes_layer + '_' + str(os.getenv('TO_DATE_TIME').split(' ')[0])

#---------------------------------------------------------------------------
# Remove NULL CSD_UIDs from output 
query = 'CSD_UID_R IS NULL OR CSD_UID_R IS NULL'
no_csd_uid = arcpy.MakeFeatureLayer_management(os.path.join(changesGDB, changes_layer), 'fl', where_clause= query)
for d in ['l', 'r']:
    direction = 'LEFT'
    print('Looking for CSD_UIDs on ' + direction.lower() + ' side')
    if d == 'r':
        direction = 'RIGHT'
    buffer = arcpy.Buffer_analysis(no_csd_uid, os.path.join(changesGDB, 'buffer_' + d), '5 METERS', direction)
    print('Making Spatial Join')
    sj = arcpy.SpatialJoin_analysis(buffer, CSD_data, os.path.join(changesGDB, d + '_sj'), join_operation= 'JOIN_ONE_TO_ONE', 
                                join_type= 'KEEP_ALL')
    joined = arcpy.AddJoin_management(no_csd_uid, 'OBJECTID', sj, 'TARGET_FID')
    print('Calculating CSD_UIDS')
    arcpy.CalculateField_management(joined, 'redline_geom.CSD_UID_' + d.upper(), '!{}.CSD_UID!'.format(d + '_sj'), 'PYTHON3')
    arcpy.RemoveJoin_management(no_csd_uid, d + '_sj')


#---------------------------------------------------------------------------
# Upload Logic

# Use pro login info as before 
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
desc = f''''Geometry changes from NGD_Redline extracted on {str(date.today())}.
Date Range: From - {os.getenv('FROM_DATE_TIME')} To - {os.getenv('TO_DATE_TIME')} 
'''
geom_flc.manager.update_definition({'description' : desc,
                                    'capabilities' : 'Query,Extract'
                                    })
#print(geom_flc.properties)
print('Sharing Layer with NGD')
geom_fl.share( groups= gis.groups.search('title:NGD')[0].groupid)
print('Upload Complete')
