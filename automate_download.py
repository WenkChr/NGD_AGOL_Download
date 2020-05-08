import os, sys, arcpy
import pandas as pd
from arcgis.gis import GIS
from arcgis.features import GeoAccessor
from arcgis.features import FeatureLayer
from dotenv import load_dotenv

arcpy.env.overwriteOutput = True

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
    arcpy.FeatureClassToFeatureClass_conversion(data_url, outGDB, outname, where_clause= query)
    return os.path.join(outGDB, outname)

def rename_the_fields(NGD_data):
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
                    'WC2021NGD_STREET_202003_NAME_SR' : 'NAME_SRC',
                    'WC2021NGD_AL_20200313_BB_UID_L' : 'BB_UID_L',
                    'WC2021NGD_AL_20200313_BB_UID_R' : 'BB_UID_R',
                    'WC2021NGD_AL_20200313_BF_UID_L' : 'BF_UID_L',
                    'WC2021NGD_AL_20200313_BF_UID_R' : 'BF_UID_R',
                    'WC2021NGD_AL_20200313_NGD_STR_U' : 'NGD_STR_UID_L',
                    'WC2021NGD_AL_20200313_NGD_STR_1' : 'NGD_STR_UID_R',
                    'WC2021NGD_AL_20200313_PLACE_ID1' : 'PLACE_ID_R',
                    'WC2021NGD_AL_20200313_ALIAS1_ST' : 'ALIAS1_STR_UID_L',
                    'WC2021NGD_AL_20200313_ALIAS1__1' : 'ALIAS1_STR_UID_R',
                    'WC2021NGD_AL_20200313_ALIAS2_ST' : 'ALIAS2_STR_UID_L',
                    'WC2021NGD_AL_20200313_ALIAS2__1' : 'ALIAS2_STR_UID_R',
                    'WC2021NGD_AL_20200313_SRC_SGMNT' : 'SRC_SGMNT_ID', 
                    'WC2021NGD_AL_20200313_SGMNT_DTE' : 'SGMNT_DTE',
                    'WC2021NGD_AL_20200313_ATTRBT_DT' : 'ATTRBT_DTE', 
                    'WC2021NGD_AL_20200313_GEOM_ACC_' : 'GEOM_ACC_CDE', 
                    'WC2021NGD_AL_20200313_AFL_DTE' : 'AFL_DTE', 
                    'WC2021NGD_AL_20200313_ATL_DTE' : 'ATL_DTE', 
                    'WC2021NGD_AL_20200313_AFR_DTE' : 'AFR_DTE',
                    'WC2021NGD_AL_20200313_ATR_DTE' : 'ATR_DTE',
                    'WC2021NGD_AL_20200313_EC_STR_ID' : 'EC_STR_ID_L', 
                    'WC2021NGD_AL_20200313_EC_STR__1' : 'EC_STR_ID_R',
                    'WC2021NGD_AL_20200313_EC_STR__2' : 'EC_STR_ID_DTE_L',
                    'WC2021NGD_AL_20200313_EC_STR__3' : 'EC_STR_ID_DTE_R',
                    'WC2021NGD_AL_20200313_LAYER_SRC' : 'LAYER_SRC_CDE',
                    'WC2021NGD_AL_20200313_LAYER_S_1' : 'LAYER_SRC_ID',
                    'WC2021NGD_AL_20200313_REVIEW_FL' : 'REVIEW_FLG',
                    'WC2021NGD_AL_20200313_MUST_HLD_' : 'MUST_HLD_TYP',
                    'WC2021NGD_AL_20200313_TRAFFIC_D' : 'TRAFFIC_DIR_CDE',
                    'WC2021NGD_AL_20200313_UPDT_SGMN' : 'UPDT_SGMNT_FLG',
                    'WC2021NGD_AL_20200313_AOI_JOB_U' : 'AOI_JOB_UID',
                    'WC2021NGD_STREET_202003_NGD_STR' : 'NGD_STR_UID',
                    'WC2021NGD_STREET_202003_CSD_UID' : 'CSD_UID',
                    'WC2021NGD_STREET_202003_STR_NME' : 'STR_NME_PRFX',
                    'WC2021NGD_STREET_202003_STR_PAR' : 'STR_PARSD_NME', 
                    'WC2021NGD_STREET_202003_STR_LAB' : 'STR_LABEL_NME', 
                    'WC2021NGD_STREET_202003_STR_STA' : 'STR_STAT_CDE',
                    'WC2021NGD_STREET_202003_UPDT_DT' : 'UPDT_DTE'}
    print('Renaming NGD fields')
    for f in arcpy.ListFields(NGD_data):
        fieldName = f.name
        if fieldName in ngdal_col_map:
            arcpy.AlterField_management(NGD_data, fieldName, ngdal_col_map[fieldName])

def unique_values(fc, field):
    # Returns a list off unique values for a given field in the unput dataset
    fl = arcpy.MakeFeatureLayer_management(fc, 'fl', where_clause= 'NGD_UID IS NOT NULL')
    with arcpy.da.SearchCursor(fc, field_names= [field]) as cursor:
        return sorted({row[0] for row in cursor})

def filter_data_remove_duplicates(Redline_data, outGDB, outName):
    # Read rows into a pandas dataframe
    df = pd.DataFrame.spatial.from_featureclass(Redline_data, sr= '3347')
    if len(df) == 0:
        print('Length of rows is 0 continuing')
        return None
    KeepRows = []
    for uid in unique_values(Redline_data, 'NGD_UID'):
        uid_rows = df.loc[df['NGD_UID'] == uid ]
        maxDateRow = uid_rows.loc[uid_rows['EditDate'] == uid_rows.EditDate.max()]
        KeepRows.append(maxDateRow.iloc[0]['OBJECTID'])
    print('Keeping ' + str(len(KeepRows)) + ' rows from Redline data')
    arcpy.FeatureClassToFeatureClass_conversion(Redline_data, 
                                                outGDB, 
                                                outName + '_uniques', 
                                                where_clause= "OBJECTID IN " + str(tuple(KeepRows)))
    return os.path.join(outGDB, outName + '_uniques')

def address_field_check(redline_data, out_gdb, out_base_name, w_NGD_UID= True):
    if arcpy.GetCount_management(redline_data) == 0:
        print('Redline data has no records returning None')
        return [None, None]
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
    print('Good rows: ' + str(len(good_rows)) + ' Rows to QC: ' + str(len(fail_rows)))
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
    #Export changes and overwrite prior redline file
    arcpy.SelectLayerByAttribute_management(fl, 'CLEAR_SELECTION')
    arcpy.FeatureClassToFeatureClass_conversion(fl, o_gdb, o_name + '_bad_addr')
    return os.path.join(o_gdb, o_name + '_bad_addr') 

def qc_PRTY_vals(redline_rows, o_gdb, o_name):
    # This needs to check every row so put after merge 
    fl = arcpy.MakeFeatureLayer_management(redline_rows, 'fl')
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
    for d in ['L', 'R']:
        
        arcpy.SelectLayerByAttribute_management(fl, 'NEW_SELECTION', where_clause= 'ADDR_PRTY_' + d + ' IS NULL')
        arcpy.CalculateField_management(fl, 'ADDR_PRTY_' + d, 'ADDR_PRTY_FIXER(!AF' + d + '_VAL!, !AT' + d + '_VAL!)', 
                                        'PYTHON3', code_block= code)
    arcpy.FeatureClassToFeatureClass_conversion(fl, o_gdb, o_name)
    return os.path.join(o_gdb, o_name)

def fix_null_src_vals(bad_redline_rows, o_gdb, o_name):
    fl = arcpy.MakeFeatureLayer_management(bad_redline_rows, 'fl')
    #Select all rows in which the F_SRC val is not null and the T_SRC val is null and make the same
    for d in ['L', 'R']:
        query1 = 'AT{}_SRC IS NULL AND AF{}_SRC IS NOT NULL'.format(d, d)
        query2 = 'AF{}_SRC IS NOT NULL AND AT{}_SRC IS NULL'.format(d, d)
        arcpy.SelectLayerByAttribute_management(fl, 'NEW_SELECTION', where_clause= query1)
        arcpy.CalculateField_management(fl, 'AT' + d +'_SRC', '!AF' + d + '_SRC!')
        arcpy.SelectLayerByAttribute_management(fl, 'NEW_SELECTION', where_clause= query2)
        arcpy.CalculateField_management(fl, 'AF' + d + '_SRC', '!AT' + d + '_SRC!')
    #Export Corrected data
    arcpy.SelectLayerByAttribute_management(fl, 'CLEAR_SELECTION')
    arcpy.FeatureClassToFeatureClass_conversion(fl, o_gdb, o_name + '_bad_addr')
    return os.path.join(o_gdb, o_name + '_bad_addr')

#------------------------------------------------------------------------------------------------------------
# inputs
load_dotenv(os.path.join(os.getcwd(), 'environments.env'))

directory = os.getcwd() # Will return the directory that this file is currently in.
url = r'https://services7.arcgis.com/bRi0AN5rG57dCDE4/arcgis/rest/services/NGD_STREET_Redline/FeatureServer' # URL for AGOL NGD_Redline data
gdb_name = 'NGD_Redline.gdb'
o_gdb = os.path.join(directory, gdb_name)
o_name = 'NGD_STREET_Redline' # Name for final output file

#Create fgdb for the downloaded data and intermediate files 
if not arcpy.Exists(o_gdb):
    print('Creating GDB')
    arcpy.CreateFileGDB_management(directory, gdb_name)

from_date = os.getenv('FROM_DATE_TIME')
to_date = os.getenv('TO_DATE_TIME')
print('Settings: From Date- {}, To Date- {}'.format(from_date, to_date))

#--------------------------------------------------------------------------------------------------------------
#Calls
print('Running script')
results = auto_download_data(url, o_gdb, o_name, from_date, to_date)
rename_the_fields(results)

if int(arcpy.GetCount_management(results).getOutput(0)) == 0:
    print('No records for given date range. Exiting script')
    sys.exit()

print('Splitting records into NGD_UIDs and Null NGD_UIDs')
w_NGD_UIDs = arcpy.FeatureClassToFeatureClass_conversion(results, o_gdb, o_name + '_w_NGD_UID', 'NGD_UID IS NOT NULL')
no_NGD_UIDs = arcpy.FeatureClassToFeatureClass_conversion(results, o_gdb, o_name + '_w_no_NGD_UID', 'NGD_UID IS NULL')

print('Records with NGD_UIDs: {}  Records with NULL NGD_UIDs: {}'.format(arcpy.GetCount_management(w_NGD_UIDs), 
                                                                        arcpy.GetCount_management(no_NGD_UIDs)))

print('Filtering to remove records that contain duplicate NGD_UIDs')
filtered = filter_data_remove_duplicates(w_NGD_UIDs, o_gdb, o_name)

print('Running address fields QC checks')
checked_w_NGD_UID = address_field_check(filtered, o_gdb, o_name + '_ch_w_uid', True)
checked_no_NGD_UID = address_field_check(no_NGD_UIDs, o_gdb, o_name + '_ch_no_uid', w_NGD_UID= False)

files = []
for fc in checked_no_NGD_UID + checked_w_NGD_UID:
    if type(fc) != None: files.append(fc)

print('Merging ' + str(len(files)) + ' files') 
merged = arcpy.Merge_management(files, os.path.join(o_gdb, o_name + '_merged'))

#Get only NGD_UIDs in redline data for NGD_AL filtering
uids = unique_values(filtered, 'NGD_UID')

outFC_nme = os.path.join(o_gdb, o_name)
print('Performing final address QC')
fix_address_field_errors(merged, o_gdb, o_name)
fix_null_src_vals(merged, o_gdb, o_name)
qc_PRTY_vals(merged, o_gdb, o_name)
print('Merging all records and exporting to final feature class')
arcpy.Merge_management(merged, os.path.join(o_gdb, o_name))

print('Deleting non essential feature classes')
arcpy.env.workspace = o_gdb
for fc in arcpy.ListFeatureClasses():
    if fc != o_name:
        arcpy.Delete_management(fc) 

print('Filtering NGD_AL data')
arcpy.FeatureClassToFeatureClass_conversion(os.path.join(directory, 'ngd_national.gdb', 'WC2021NGD_AL_20200313'),
                                            os.path.join(directory, o_gdb), 
                                            'WC2021NGD_AL_20200313',
                                            'NGD_UID IN ' + str(tuple(uids)))  

print('DONE!')
