import os
import sys

import arcpy
from arcpy.arcobjects.arcobjects import Row
import pandas as pd
import numpy as np
from arcgis.features import FeatureLayer, GeoAccessor
from arcgis.gis import GIS
from arcgis import features
from dotenv import load_dotenv

arcpy.env.overwriteOutput = True
# Compare Redline against the NGD_AL and check topology initially for overlaps that make no sense.
# Take the overlaps output into a new QC layer with an issue field tagged in the output

def RangeOverlapDetection(AF_VAL, AT_VAL, AL_AF, AL_AT ): 
    # Compares the OA range and the NGD range in matches and return a set class value for easy comparison    
    vals =[AF_VAL, AT_VAL, AL_AF, AL_AT]
    if AF_VAL > AT_VAL:
        # Then AF pairs with min and AT pairs with max
        vals = [AT_VAL, AF_VAL, AL_AT, AL_AF]
    if (vals[0] <= vals[3]) and (vals[2] <= vals[1]):
        return 'overlap'

        
#-------------------------------------------------------------------------------------------------
# Inputs

url = r'https://services7.arcgis.com/bRi0AN5rG57dCDE4/arcgis/rest/services/NGD_STREET_Redline_V2_61/FeatureServer/0' # URL for AGOL NGD_Redline data
#url = r'https://services7.arcgis.com/bRi0AN5rG57dCDE4/arcgis/rest/services/NGD_STREET_Redline_V2_6/FeatureServer/0' # URL for the test NGD_Redline data
line_errors_url = r'https://services7.arcgis.com/bRi0AN5rG57dCDE4/arcgis/rest/services/Redline_Topo_Line_Errors/FeatureServer/0'

workingDirectory = r'H:\NGD_AGOL_Download'
working_gdb = os.path.join(workingDirectory, 'Default.gdb')
NGD_AL = r'H:\NGD_AGOL_Download\Final_Export_2020-09-28_2.gdb\NGD_AL'

downloaded_redline_name = 'NGD_Redline'
errors_out_basename = 'Redline_Topo'
#-------------------------------------------------------------------------------------------------
#Logic

#Download the red line
gis = GIS('pro')
print('Logged in as: ' + str(gis.properties.user.username))

if os.path.split(url)[1] != '0': # Ensure URL ends in \0 just an AGOL thing
    data_url = os.path.join(url, '0')

#query = "EditDate BETWEEN TIMESTAMP '{}' AND TIMESTAMP '{}'".format(from_date, to_date)
arcpy.FeatureClassToFeatureClass_conversion(url, working_gdb, downloaded_redline_name) #, where_clause= query)
redlineToCheck = os.path.join(working_gdb, downloaded_redline_name)

redline_df = pd.DataFrame.spatial.from_featureclass(os.path.join(working_gdb, downloaded_redline_name))
redline_df = redline_df[redline_df['NGD_UID'].notna()] # Drop null NGD_UIDs
print(f'Checking {len(redline_df)} redline records')

print('Loading in all NGD_AL records')
where = f"NGD_STR_UID_L IN {tuple(redline_df.NGD_STR_UID_L.unique().tolist())} OR NGD_STR_UID_R IN {tuple(redline_df.NGD_STR_UID_R.unique().tolist())} AND NGD_UID IN {tuple(redline_df.NGD_UID.unique().tolist())}"
NGD_AL_df = pd.DataFrame.spatial.from_featureclass(NGD_AL, where_clause= where)
print(f'Loaded in {len(NGD_AL)} NGD_AL records')

overlap_Rows = []
for row in redline_df.itertuples():
    # for each row check ranges associated with NGD_STR_UID_L and R 
    print(f'Checking for address overlaps NGD_UID: {row.NGD_UID}')
    for side in ['L', 'R']:
        # Get column index values
        STR_UID_index = redline_df.columns.get_loc(f'NGD_STR_UID_{side}') + 1 
        AF_index = redline_df.columns.get_loc(f'AF{side}_VAL') + 1 
        AT_index = redline_df.columns.get_loc(f'AT{side}_VAL') + 1 
        
        # Extract specific row values from indexes above
        NGD_STR_UID = row[STR_UID_index]
        AF_val = row[AF_index]
        AT_val = row[AT_index]
        # Check for null ranges in the redline address range
        if (AF_val is None or AT_val is None) or (np.isnan(AF_val) or np.isnan(AT_val)): continue 

        NGD_AL_df = pd.DataFrame.spatial.from_featureclass(NGD_AL, where_clause= f"NGD_STR_UID_{side} = {NGD_STR_UID} AND NGD_UID <> {row.NGD_UID}") # Extract all rows from the NGD_AL with the same NGD_STR_UID
       

        for al_row in NGD_AL_df.itertuples(): # Iterate over the rows in the NGD_AL df and check for overlaps
            #Extract key values from the NGD_AL row
            AL_AF_val = al_row[NGD_AL_df.columns.get_loc(f'AF{side}_VAL') + 1]
            AL_AT_val = al_row[NGD_AL_df.columns.get_loc(f'AT{side}_VAL') + 1]                         

            if (AL_AF_val is None or AL_AT_val is None) or (np.isnan(AL_AF_val) or np.isnan(AL_AT_val)): continue # If both key values are null or nontype then skip to next record
            print(AF_val, AT_val)
            print(AL_AF_val, AL_AT_val)
            flag = RangeOverlapDetection(int(AF_val), int(AT_val), int(AL_AF_val), int(AL_AT_val))

            if flag == 'overlap':      
                out = [row.NGD_UID, AF_val, AT_val, al_row.NGD_UID, AL_AF_val, AL_AT_val, f'overlap on {side}', row.SHAPE]
                overlap_Rows.append(out) # append the NGD_UID to the overlap list for export
            
out_df = pd.DataFrame(overlap_Rows, columns=['Redline_NGD_UID', 'Redline_AF_VAL', 'Redline_AT_VAL', 'AL_NGD_UID', 'AL_AF_VAL', 'AL_AT_VAL', 'overlap_flag', 'SHAPE'])
out_df = pd.DataFrame.spatial.from__df(out_df, geometry_column= 'SHAPE')

out_df.to_featureclass(os.path.join(working_gdb, 'overlap_test'))
# print('Prepping results for upload to AGOL')

# errors_df = pd.DataFrame.spatial.from_featureclass(os.path.join(working_gdb, errors_out_basename + '_line'), sr= '3347')

# if len(errors_df) == 0:
#     print(f'Length of errors fc is: {len(errors_df)}. Exiting script.')
#     sys.exit()
     
# append_list = []

# for row in errors_df.itertuples():
#     outrow = {"attributes": 
#             {'OriginObjectClassName' : row.OriginObjectClassName,
#             'OriginObjectID' : row.OriginObjectID,
#             'DestinationObjectClassName' : row.DestinationObjectClassName,
#             'DestinationObjectID' : row.DestinationObjectID,
#             'RuleType' : row.RuleType,
#             'RuleDescription': row.RuleDescription,
#             'isException': row.isException,
#             'geometry': row.SHAPE
#             }}
#     append_list.append(outrow)
# print('Loading in errors_fl by its unique url')
# errors_fl = features.FeatureLayer(line_errors_url)

# errors_fl.edit_features(adds=append_list)
print('DONE!')
