import os, sys, arcpy
from arcgis.gis import GIS

arcpy.env.overwriteOutput = True

def auto_download_data(data_url, outGDB, outname, att_or_geo, fieldPrefix= 'WC2021NGD_AL_20200313_'):
    """ Requires you to be logged into arcgis pro on this computer with an account that has access to the data you are trying to 
    download. You must be logged into arcGIS pro with your statscan AGOL account in order for this to work. This funtion will
    go into the NGD group via the arcGIS portal and download a specific feature layer as determined by the variable"""
    #Verify credentials
    gis = GIS('pro')
    print('Logged in as: ' + str(gis.properties.user.username))
    
    if os.path.split(data_url)[1] != '0':
        data_url = os.path.join(data_url, '0')
    
    if att_or_geo:
        arcpy.FeatureClassToFeatureClass_conversion(data_url, outGDB, outname, whereClause= fieldPrefix + "NGD_UID IS NOT NULL")
    if not att_or_geo:
        arcpy.FeatureClassToFeatureClass_conversion(data_url, outGDB, outname, whereClause= fieldPrefix + "NGD_UID IS NULL")
    return os.path.join(outGDB, outname)

def unique_values(fc, field):
    # Returns a list off unique values for a given field in the unput dataset
    with arcpy.da.SearchCursor(fc, field_names= [field]) as cursor:
        return sorted({row[0] for row in cursor})

def filter_data_remove_duplicates(Redline_data, outGDB, outName, field_prefix= 'WC2021NGD_AL_20200313_'):
    # Start by finding the most recent date for each NGD_UID and keeping only that date
    KeepRows = []
    for uid in unique_values(Redline_data, field_prefix + 'NGD_UID'):
        fieldnames = [field_prefix + 'NGD_UID', 'EditDate']
        fl = arcpy.MakeFeatureLayer_management(Redline_data, 'fl', where_clause= fieldnames[0] + '= ' + str(uid))
        max_date = max(unique_values(fl, fieldnames[1]))
        with arcpy.da.SearchCursor(fl, field_names= ['OBJECTID', fieldnames[1]]) as cursor:
            for row in cursor:
                if row[1] == max_date:
                    KeepRows.append(row[0])
    fl = arcpy.MakeFeatureLayer_management(Redline_data, 'fl2')
    for oid in KeepRows:
        arcpy.SelectLayerByAttribute_management(fl, 'ADD_TO_SELECTION', "OBJECTID = {}".format(oid))
    arcpy.FeatureClassToFeatureClass_conversion(fl, outGDB, outName)
    return os.path.join(outGDB, outName)

# inputs

url = r'https://services7.arcgis.com/bRi0AN5rG57dCDE4/arcgis/rest/services/NGD_STREET_Redline/FeatureServer'
file_name = 'NGD_STREET Redline'
o_gdb = r'H:\automate_AGOL_download\AGOL_tests.gdb'
o_name = 'RedLine'

#Calls

results = auto_download_data(url, file_name, o_gdb, o_name)
filtered = filter_data_remove_duplicates(results, o_gdb, 'Redline_w_NGD_UID')

print('DONE!')

    # group = gis.groups.search('title: ' + group) [0]
    # items = group.content()
    # item_to_download = [d_item for d_item in items if d_item.title == file_name]
    # if len(item_to_download) == 0:
    #     print('No items of that name exist. Try again')
    #     return None
    # item_url = item_to_download[0].url
    # o_file = gis.content.get(item_url)