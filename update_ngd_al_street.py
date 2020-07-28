import os, sys, arcpy
import pandas as pd
from arcgis import GeoAccessor

''' Workflow Overview
1.) Bring in NGD_AL and NGD_STREET data
2.) Create join between NGD_AL and NGD_STREET on NGD_STR_UID_L
3.) Create join on ALIAS_1_STR_UID_L field and add the street name, street type, street direction by again joining NGD_STREET to NGD_AL
4.) Repeat step 3 for ALIAS 2 rename fields for both aliases appropriately
5.) Upload to AGOL and share with NGD group
'''
#-------------------------------------------------------------------------------------------------------------------------------------
#Functions

def table_to_data_frame(in_table, input_fields=None, where_clause=None):
    """Function will convert an arcgis table into a pandas dataframe with an object ID index, and the selected
    input fields using an arcpy.da.SearchCursor."""
    OIDFieldName = arcpy.Describe(in_table).OIDFieldName
    if input_fields:
        final_fields = [OIDFieldName] + input_fields
    else:
        final_fields = [field.name for field in arcpy.ListFields(in_table)]
    data = [row for row in arcpy.da.SearchCursor(in_table, final_fields, where_clause=where_clause)]
    fc_dataframe = pd.DataFrame(data, columns=final_fields)
    fc_dataframe = fc_dataframe.set_index(OIDFieldName, drop=True)
    return fc_dataframe
#-------------------------------------------------------------------------------------------------------------------------------------
#Constants

#NGD_AL_fc = r'H:\NGD_AGOL_Download\Final_Export_2020-05-29_2.gdb\WC2021NGD_AL_20200313_'
NGD_STREET_tbl = r'H:\NGD_AGOL_Download\NGD_Redline.gdb\NGD_STREET'
NGD_AL_fc = r'H:\NGD_AGOL_Download\NGD_Redline.gdb\al_aliastest'
#-------------------------------------------------------------------------------------------------------------------------------------
#Logic
print('Loading in NGD_AL and NGD_STREET')
AL_df = pd.DataFrame.spatial.from_featureclass(NGD_AL_fc)
STREET_df = table_to_data_frame(NGD_STREET_tbl, ['NGD_STR_UID', 'STR_NME', 'STR_TYP', 'STR_DIR', 'NAME_SRC'])
print('Merging NGD_AL and NGD_STREET')
aliased = pd.DataFrame()
for alias in ['ALIAS1', 'ALIAS2']:
    AL_alias = AL_df.loc[AL_df[f'{alias}_STR_UID_L'] != 0]
    aliasStreet = STREET_df
    aliasStreet.rename(columns= {'STR_NME' : f'STR_NME_{alias}', 
                                'STR_TYP' : f'STR_TYP_{alias}',
                                'STR_DIR' : f'STR_DIR_{alias}',
                                'STR_NME' : f'STR_NME_{alias}'},
                                inplace= True) # Rename NGD_STREET fields to match the alias that they are replacing
    merged = pd.merge(AL_alias, aliasStreet, left_on= f'{alias}_STR_UID_L', right_on= 'NGD_STR_UID' )
    print(merged.head())
    sys.exit()
print('DONE!')
