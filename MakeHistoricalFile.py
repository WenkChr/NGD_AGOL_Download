import os, sys, arcpy
import pandas as pd
from arcgis.gis import GIS
from arcgis.features import GeoAccessor
from arcgis.features import FeatureLayer
from dotenv import load_dotenv

arcpy.env.overwriteOutput = True
'''
This script takes a from and to date from the NGD_Redline data and uploads the dataset as a historical file to AGOL shared with the NGD
Group. This is for the purposes of clearing prior edits from the redline so new edits can be made. The historical file retains the deleted 
records for metrics and record keeping.
'''

#-------------------------------------------------------------------------------------------------------------------------------------
#Functions
def auto_download_data(data_url, outGDB, outname, from_date, to_date):
    """ Requires you to be logged into arcgis pro on this computer with an account that has access to the data you are trying to 
    download. You must be logged into arcGIS pro with your statscan AGOL account in order for this to work. This funtion will
    go into the NGD group via the arcGIS portal and download a specific feature layer as determined by the variable. Date format
    for the from and too dates are YYYY-MM-DD. Do not include a timestamp as that will cause errors"""
    #Verify credentials
    gis = GIS('pro')
    print('Logged in as: ' + str(gis.properties.user.username))
    
    if os.path.split(data_url)[1] != '0':
        data_url = os.path.join(data_url, '0')
    
    query = "EditDate BETWEEN TIMESTAMP '{}' AND TIMESTAMP '{}'".format(from_date, to_date)
    if arcpy.Exists(os.path.join(outGDB, outname)):
        arcpy.Delete_management(os.path.join(outGDB, outname))
    arcpy.FeatureClassToFeatureClass_conversion(data_url, outGDB, outname, where_clause= query)
    return os.path.join(outGDB, outname)

#--------------------------------------------------------------------------------------------------------------------------
#Inputs
url = r'https://services7.arcgis.com/bRi0AN5rG57dCDE4/arcgis/rest/services/NGD_STREET_Redline_V2_6/FeatureServer/0' #Set to test redline
gdb_name = 'NGD_Redline.gdb'
out_name = 'HistoricalFile'
from_date = '2020-10-26 8:00:01'
to_date =  '2020-10-20 17:00:00'
query = "EditDate BETWEEN TIMESTAMP '{}' AND TIMESTAMP '{}'".format(from_date, to_date)
#-----------------------------------------------------------------------------------------------------------------------------
#Logic
print('Making historical layer')
hist_fc = auto_download_data(url, gdb_name, out_name, from_date, to_date) #Create the historical feature layer
print('Historical layer creation complete')
gis = GIS('pro')

fl_item = FeatureLayer(url)
fl_item.delete_features(where= query)
print('DONE!')
