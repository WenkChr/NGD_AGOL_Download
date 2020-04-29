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
    print('Renaming redline fields')
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
            return os.path.join(outGDB, outName)
        fieldnames = ['NGD_UID', 'EditDate']
        fl = arcpy.MakeFeatureLayer_management(Redline_data, 'fl', where_clause= fieldnames[0] + '= ' + str(uid))
        max_date = max(unique_values(fl, fieldnames[1]))
        with arcpy.da.SearchCursor(fl, field_names= ['OBJECTID', fieldnames[1]]) as cursor:
            for row in cursor:
                if row[1] == max_date:
                    KeepRows.append(row[0])
    fl = arcpy.MakeFeatureLayer_management(Redline_data, 'fl2')    
    arcpy.SelectLayerByAttribute_management(fl, where_clause= "OBJECTID IN " + str(tuple(KeepRows)))
    arcpy.FeatureClassToFeatureClass_conversion(fl, outGDB, outName + '_uniques')
    return os.path.join(outGDB, outName)

def address_field_check(redline_data, out_gdb, out_base_name, w_NGD_UID= True):
    print('Running address field changes check')
    # check redline fields against the NGD_AL fields. If fields change from valid to invalid flag those rows
    uid_field = 'NGD_UID'
    if w_NGD_UID == False:
        uid_field = 'OBJECTID'
    
    fields_to_qc = [uid_field, 'AFL_VAL','AFL_SRC', 'AFR_VAL', 'AFR_SRC', 'ATL_VAL', 'ATL_SRC', 'ATR_VAL', 'ATR_SRC', 'ADDR_TYP_L',
                    'ADDR_TYP_R', 'ADDR_PRTY_L', 'ADDR_PRTY_R']
    
    fail_rows = []
    good_rows = []
    with arcpy.da.SearchCursor(redline_data, field_names= fields_to_qc ) as cursor:
        for row in cursor:
            #If the row breaks the rule then add to the fail_rows list for correction
            #if AFL_VAL IS NOT NULL THEN ATL_VAL, ADDR_TYP_L, ADDR_PRTY_L NOT NULL
            if row[1] != None and row[5] == None or  row[9] == None or row[11] == None:
                fail_rows.append(row[0])
                continue
            #if ATL_VAL IS NOT NULL THEN AFL_VAL ADDR_TYP_L, ADDR_PRTY_L NOT NULL
            if row[5] != None and row[1] == None or  row[9] == None or row[11] == None:
                fail_rows.append(row[0])
                continue
            # if AFR_VAL not NULL, then ATR_VAL, ADDR_TYP_R, ADDR_PRTY_R not NULL 
            if row[3] != None and row[7] == None or row[10] == None or row[12] == None:
                fail_rows.append(row[0])
                continue
            #if ATR_VAL not NULL, then AFR_VAL, ADDR_TYP_R, ADDR_PRTY_R not NULL 
            if row[7] != None and row[3] == None or row[10] == None or row[12] == None:
                fail_rows.append(row[0])
                continue
            good_rows.append(row[0])
    print('Exporting sorted rows')
    outlist = [None, None]
    
    if len(good_rows) > 0:
        arcpy.FeatureClassToFeatureClass_conversion(redline_data, out_gdb, out_base_name + '_goodAddr',  
                                                    where_clause= uid_field + ' IN ' + str(tuple(good_rows)))
        outlist[0] = os.path.join(out_gdb, out_base_name + '_goodAddr')
    if len(fail_rows)> 0:
        arcpy.FeatureClassToFeatureClass_conversion(redline_data, out_gdb, out_base_name + '_badAddr',  
                                                    where_clause= uid_field + ' IN ' + str(tuple(fail_rows)))
        outlist[1] = os.path.join(out_gdb, out_base_name + '_badAddr')
    return outlist


def fix_address_field_errors(bad_redline_rows, o_gdb, o_name):
    fl = arcpy.MakeFeatureLayer_management(bad_redline_rows, 'fl')
    for d in ['L', 'R']:
        #Fill in AF and AT holes
        query1 = 'AT{}_VAL IS NULL AND AF{}_VAL IS NOT NULL'.format(d, d)
        query2 = 'AT{}_VAL IS NOT NULL AND AF{}_VAL IS NULL'.format(d, d)
        arcpy.SelectLayerByAttribute_management(fl, where_clause= query1)
        arcpy.CalculateField_management(fl, 'AT' + d + '_VAL', '!AF' + d + '_VAL!')
        arcpy.SelectLayerByAttribute_management(fl, 'NEW_SELECTION', query2)
        arcpy.CalculateField_management(fl, 'AF' + d + '_VAL', '!AT' + d + '_VAL!')
        code = '''
def ADDR_PRTY_FIXER(AF_VAL, AT_VAL):
    AF_int = int(AF_VAL)
    AT_int = int(AT_VAL)
    if (AF_int % 2) == 0 and (AT_int % 2) == 0:
        return 'E'
    if (AF_int % 2) != 0 and (AT_int % 2) != 0:
        return 'O'
    if (AF_int % 2) == 0 and (AT_int % 2) != 0:
        return 'M'
    if (AF_int % 2) != 0 and (AT_int % 2) == 0:
        return 'M'
        '''
        arcpy.SelectLayerByAttribute_management(fl, 'NEW_SELECTION', where_clause= 'ADDR_PRTY_' + d + ' IS NULL')
        arcpy.CalculateField_management(fl, 'ADDR_PRTY_' + d, 'ADDR_PRTY_FIXER(!AF' + d + '_VAL!, !AT' + d + '_VAL!)', 
                                        'PYTHON3', code_block= code)    
    #Export changes and overwrite prior redline file
    arcpy.SelectLayerByAttribute_management(fl, 'CLEAR_SELECTION')
    arcpy.FeatureClassToFeatureClass_conversion(fl, o_gdb, o_name + '_bad_addr')
    return os.path.join(o_gdb, o_name + '_bad_addr') 

def delete_non_essentials(gdb, keepFile_name):
    #Deletes contents of a GDB except for the specified keep file
    arcpy.env.workspace = gdb
    print('Deleting intermediate files')    
    fcs = arcpy.ListFeatureClasses()
    if len(fcs)> 0 and type(fcs) != None:
        for f in arcpy.ListFeatureClasses(gdb):
            if arcpy.Exists(f) and f != keepFile_name:
                arcpy.Delete_management(f)

#------------------------------------------------------------------------------------------------------------
# inputs

directory = os.getcwd() # Will return the directory that this file is currently in.
url = r'https://services7.arcgis.com/bRi0AN5rG57dCDE4/arcgis/rest/services/NGD_STREET_Redline/FeatureServer' # URL for AGOL NGD_Redline data
gdb_name = 'NGD_Redline.gdb'
o_gdb = os.path.join(directory, gdb_name)
o_name = 'NGD_STREET_Redline' # Name for final output file

#Create fgdb for the downloaded data and intermediate files 
if not arcpy.Exists(o_gdb):
    arcpy.CreateFileGDB_management(directory, gdb_name)

print('Input whether you want allrecords with NGD_UIDs (True) or all records without (False):')
NGD_UIDs = input()

print('Indicate the date you want records extraction to start at (format: YYYY-MM-DD):')
from_date = input()
print('Indicate the date you want records extraction to end on (format: YYYY-MM-DD):')
to_date = input()

#--------------------------------------------------------------------------------------------------------------
#Calls
print('Running script')
results = auto_download_data(url, o_gdb, o_name, NGD_UIDs, from_date, to_date)
rename_the_fields(results)
print('Filtering to remove duplicate records (only when running on records that contain NGD_UIDs)')
filtered = filter_data_remove_duplicates(results, o_gdb, o_name)
print('Running address fields QC checks')
checked = address_field_check(filtered, o_gdb, o_name, NGD_UIDs)

print('Merging all records and exporting to final feature class')
if checked[1] == None:
    arcpy.FeatureClassToFeatureClass_conversion(checked[0], o_gdb, o_name)
    delete_non_essentials(o_gdb, o_name)
if checked[1] != None:
    fix_address_field_errors(checked[1], o_gdb, o_name)
    arcpy.Delete_management(os.path.join(o_gdb, o_name))
    if checked[0] != None:
        arcpy.Merge_management(checked, os.path.join(o_gdb, o_name))
        delete_non_essentials(o_gdb, o_name)
    else: 
        arcpy.FeatureClassToFeatureClass_conversion(checked[1], o_gdb, o_name)
        delete_non_essentials(o_gdb, o_name)

print('DONE!')
