import os, sys, arcpy
from arcgis.gis import GIS
from arcgis.features import FeatureLayer
arcpy.env.overwriteOutput = True

def auto_download_data(data_url, outGDB, outname, att_or_geo, from_date, to_date, fieldPrefix= 'WC2021NGD_AL_20200313_'):
    """ Requires you to be logged into arcgis pro on this computer with an account that has access to the data you are trying to 
    download. You must be logged into arcGIS pro with your statscan AGOL account in order for this to work. This funtion will
    go into the NGD group via the arcGIS portal and download a specific feature layer as determined by the variable. Date format
    for the from and too dates are YYYY-MM-DD. Do not include a timestamp as that will cause errors"""
    #Verify credentials
    gis = GIS('pro')
    print('Logged in as: ' + str(gis.properties.user.username))
    
    if os.path.split(data_url)[1] != '0':
        data_url = os.path.join(data_url, '0')
    
    #layer = FeatureLayer(data_url)
    #layer_date_query = layer.query(where= "EditDate BETWEEN DATE '2020-04-10' AND DATE '2020-04-15'")
    if att_or_geo:
        query = fieldPrefix + "NGD_UID IS NOT NULL AND EditDate BETWEEN DATE '{}' AND DATE '{}'".format(from_date, to_date)
        arcpy.FeatureClassToFeatureClass_conversion(data_url, outGDB, outname, where_clause= query)
    if not att_or_geo:
        query = fieldPrefix + "NGD_UID IS NULL AND EditDate BETWEEN DATE '{}' AND DATE '{}'".format(from_date, to_date)
        arcpy.FeatureClassToFeatureClass_conversion(data_url, outGDB, outname, where_clause= fieldPrefix + "NGD_UID IS NULL")
    return os.path.join(outGDB, outname)

def rename_the_fields(redline_data):
    ngdal_col_map = {'WC2021NGD_AL_20200313_NGD_UID': 'NGD_UID',
                    'WC2021NGD_AL_20200313_SGMNT_TYP': 'SGMNT_TYP_CDE',
                    'WC2021NGD_AL_20200313_SGMNT_SRC': 'SGMNT_SRC',
                    'WC2021NGD_AL_20200313_STR_CLS_C': 'STR_CLS_CDE',
                    'WC2021NGD_AL_20200313_STR_RNK_C': 'STR_RNK_CDE',
                    'WC2021NGD_AL_20200313_AFL_VAL': 'AFL_VAL',
                    'WC2021NGD_AL_20200313_AFL_SFX': 'AFL_SFX',
                    'WC2021NGD_AL_20200313_AFL_SRC': 'AFL_SRC',
                    'WC2021NGD_AL_20200313_ATL_VAL': 'ATL_VAL',
                    'WC2021NGD_AL_20200313_ATL_SFX': 'ATL_SFX',
                    'WC2021NGD_AL_20200313_ATL_SRC': 'ATL_SRC',
                    'WC2021NGD_AL_20200313_AFR_VAL': 'AFR_VAL',
                    'WC2021NGD_AL_20200313_AFR_SFX': 'AFR_SFX',
                    'WC2021NGD_AL_20200313_AFR_SRC': 'AFR_SRC',
                    'WC2021NGD_AL_20200313_ATR_VAL': 'ATR_VAL',
                    'WC2021NGD_AL_20200313_ATR_SFX': 'ATR_SFX',
                    'WC2021NGD_AL_20200313_ATR_SRC': 'ATR_SRC',
                    'WC2021NGD_AL_20200313_ADDR_TYP_': 'ADDR_TYP_L',
                    'WC2021NGD_AL_20200313_ADDR_TYP1': 'ADDR_TYP_R',
                    'WC2021NGD_AL_20200313_ADDR_PRTY': 'ADDR_PRTY_L',
                    'WC2021NGD_AL_20200313_ADDR_PR_1': 'ADDR_PRTY_R',
                    'WC2021NGD_AL_20200313_NGD_STR_2': 'NGD_STR_UID_DTE_L',
                    'WC2021NGD_AL_20200313_NGD_STR_3' : 'NGD_STR_UID_DTE_R',
                    'WC2021NGD_AL_20200313_CSD_UID_L' : 'CSD_UID_L',
                    'WC2021NGD_AL_20200313_CSD_UID_R' : 'CSD_UID_R',
                    'WC2021NGD_AL_20200313_PLACE_ID_' : 'PLACE_ID_L',
                    'WC2021NGD_AL_20200313_PLACE_ID_1' : 'PLACE_ID_R',
                    'WC2021NGD_AL_20200313_PLACE_I_1' : 'PLACE_ID_L_PREV',
                    'WC2021NGD_AL_20200313_PLACE_I_2' : 'PLACE_ID_R_PREC', 
                    'WC2021NGD_AL_20200313_NAME_SRC_' : 'NAME_SRC_L',
                    'WC2021NGD_AL_20200313_NAME_SRC1' : 'NAME_SRC_R',
                    'WC2021NGD_AL_20200313_FED_NUM_L' : 'FED_NUM_L',
                    'WC2021NGD_AL_20200313_FED_NUM_R' : 'FED_NUM_R',
                    'WC2021NGD_STREET_202003_STR_N_1' : 'STR_NME',
                    'WC2021NGD_STREET_202003_STR_TYP' : 'STR_TYP',
                    'WC2021NGD_STREET_202003_STR_DIR' : 'STR_DIR',
                    'WC2021NGD_STREET_202003_NAME_SR' : 'NAME_SR',
                    'WC2021NGD_AL_20200313_BB_UID_L' : 'BB_UID_L',
                    'WC2021NGD_AL_20200313_BB_UID_R' : 'BB_UID_R',
                    'WC2021NGD_AL_20200313_BF_UID_L' : 'BF_UID_L',
                    'WC2021NGD_AL_20200313_BF_UID_R' : 'BF_UID_R',
                    'WC2021NGD_AL_20200313_NGD_STR_U' : 'NGD_STR_UID_L',
                    'WC2021NGD_AL_20200313_NGD_STR_1' : 'NGD_STR_UID_R',
                    'WC2021NGD_AL_20200313_PLACE_ID1' : 'PLACE_ID_R'}
    print('Renaming  redline fields')
    for f in arcpy.ListFields(redline_data):
        fieldName = f.name
        if fieldName in ngdal_col_map:
            arcpy.AlterField_management(redline_data, fieldName, ngdal_col_map[fieldName])


def unique_values(fc, field):
    # Returns a list off unique values for a given field in the unput dataset
    with arcpy.da.SearchCursor(fc, field_names= [field]) as cursor:
        return sorted({row[0] for row in cursor})

def filter_data_remove_duplicates(Redline_data, outGDB, outName):
    # Start by finding the most recent date for each NGD_UID and keeping only that date
    KeepRows = []
    for uid in unique_values(Redline_data, 'NGD_UID'):
        if uid == None:
            print('NGD_UID is None no filtering required')
            break
        fieldnames = ['NGD_UID', 'EditDate']
        fl = arcpy.MakeFeatureLayer_management(Redline_data, 'fl', where_clause= fieldnames[0] + '= ' + str(uid))
        max_date = max(unique_values(fl, fieldnames[1]))
        with arcpy.da.SearchCursor(fl, field_names= ['OBJECTID', fieldnames[1]]) as cursor:
            for row in cursor:
                if row[1] == max_date:
                    KeepRows.append(row[0])
    fl = arcpy.MakeFeatureLayer_management(Redline_data, 'fl2')    
    arcpy.SelectLayerByAttribute_management(fl, where_clause= "OBJECTID IN " + str(tuple(KeepRows)))
    arcpy.FeatureClassToFeatureClass_conversion(fl, outGDB, outName)
    return os.path.join(outGDB, outName)

def address_field_check(redline_data, out_gdb, out_base_name):
    print('running address field changes check')
    # check redline fields against the NGD_AL fields. If fields change from valid to invalid flag those rows
    fields_to_qc = ['NGD_UID','AFL_VAL','AFL_SRC', 'AFR_VAL', 'AFR_SRC', 'ATL_VAL', 'ATL_SRC', 'ATR_VAL', 'ATR_SRC', 'ADDR_TYP_',
                    'ADDR_TYP1', 'ADDR_PRTY', 'ADDR_PR_1'] # ADDR_PRTY is ADDR_PRTY_L and ADDR_PR_1 is ADDR_PRTY_R TYP_ is L and TYP1 is R
    # filter NGD_AL so that it only contains those NGD_UIDs contained in the Redline
    fail_rows = []
    good_rows = []
    with arcpy.da.SearchCursor(redline_data, field_names= fields_to_qc ) as cursor:
        for row in cursor:
            # if AFL_VAL IS NOT NULL THEN ATL_VAL, ADDR_TYP_L, ADDR_PRTY_L NOT NULL
            if row[1] != None and row[5] == None or  row[9] == None or row[11] == None:
                print(row)
                fail_rows.append(row[0])
                continue
            # if ATL_VAL IS NOT NULL THEN AFL_VAL ADDR_TYP_L, ADDR_PRTY_L NOT NULL
            if row[5] != None and row[1] == None or  row[9] == None or row[11] == None:
                fail_rows.append(row[0])
                continue
            good_rows.append(row[0])
    print('exporting sorted rows')
    arcpy.FeatureClassToFeatureClass_conversion(redline_data, out_gdb, out_base_name + '_goodAddr',  
                                                where_clause= 'NGD_UID IN' + str(tuple(good_rows)))
    arcpy.FeatureClassToFeatureClass_conversion(redline_data, out_gdb, out_base_name + '_badAddr',  
                                                where_clause= 'NGD_UID IN' + str(tuple(fail_rows)))




# inputs

url = r'https://services7.arcgis.com/bRi0AN5rG57dCDE4/arcgis/rest/services/NGD_STREET_Redline/FeatureServer'
file_name = 'NGD_STREET Redline'
o_gdb = r'H:\automate_AGOL_download\AGOL_tests.gdb'
o_name = 'RedLine_datetest'

#Calls
print('Running calls')
results = auto_download_data(url, o_gdb, o_name, True, '2020-04-10', '2020-04-15')
rename_the_fields(results)
print('Filtering')
filtered = filter_data_remove_duplicates(results, o_gdb, 'Redline_w_NGD_UID')
print('Running address field QC checks')
#address_field_check(filtered, o_gdb, o_name)
print('DONE!')
