import os, sys, arcpy
from arcgis.gis import GIS
from zipfile import ZipFile

arcpy.env.overwriteOutput = True

def auto_download_data(data_url, file_name, outGDB, outname):
    """ Requires you to be logged into arcgis pro on this computer with an account that has access to the data you are trying to 
    download. You must be logged into arcGIS pro with your statscan AGOL account in order for this to work. This funtion will
    go into the NGD group via the arcGIS portal and download a specific feature layer as determined by the file_name variable"""
    #Verify credentials
    gis = GIS('pro')
    print('Logged in as: ' + str(gis.properties.user.username))
    
    if os.path.split(data_url)[1] != '0':
        data_url = os.path.join(data_url, '0')
    
    arcpy.FeatureClassToFeatureClass_conversion(data_url, outGDB, outname)
    return os.path.join(outGDB, outname)
    

def filter_data_NGD_Redline(Redline_data, outGDB):
    fl = arcpy.MakeFeatureLayer_management(Redline_data, 'fl')
    arcpy.SelectLayerByAttribute_management(fl, where_clause= "NGD_UID IS NOT NULL")
    

# inputs

url = r'https://services7.arcgis.com/bRi0AN5rG57dCDE4/arcgis/rest/services/NGD_STREET_Redline/FeatureServer'
file_name = 'NGD_STREET Redline'
o_gdb = r'H:\automate_AGOL_download\AGOL_tests.gdb'
o_name = 'RedLine'

#Calls

results = auto_download_data(url, file_name, o_gdb, o_name)
filtered = filter_data_NGD_Redline(results, o_gdb)

print('DONE!')

    # group = gis.groups.search('title: ' + group) [0]
    # items = group.content()
    # item_to_download = [d_item for d_item in items if d_item.title == file_name]
    # if len(item_to_download) == 0:
    #     print('No items of that name exist. Try again')
    #     return None
    # item_url = item_to_download[0].url
    # o_file = gis.content.get(item_url)