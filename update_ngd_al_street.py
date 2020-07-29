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
NGD_AL_fc = r'H:\NGD_AGOL_Download\Final_Export_2020-05-29_2.gdb\WC2021NGD_AL_20200313_'
#-------------------------------------------------------------------------------------------------------------------------------------
#Logic
print('Loading in NGD_AL')
AL_df = pd.DataFrame.spatial.from_featureclass(NGD_AL_fc, fields= ['NGD_UID', 'NGD_STR_UID_L', 
                                                                'ALIAS1_STR_UID_L', 
                                                                'ALIAS2_STR_UID_L'])

print('Merging NGD_AL and NGD_STREET')
for alias in ['ALIAS1', 'ALIAS2']:
    print(f'Aliasing {alias} fields')
    print('Loading in NGD_STREET')
    aliasStreet = table_to_data_frame(NGD_STREET_tbl, ['NGD_STR_UID', 'STR_NME', 'STR_TYP', 'STR_DIR', 'NAME_SRC'])
    aliasStreet.rename(columns= {'NGD_STR_UID' : f'{alias}_NGD_STR_UID',
                                'STR_NME' : f'{alias}_STR_NME', 
                                'STR_TYP' : f'{alias}_STR_TYP',
                                'STR_DIR' : f'{alias}_STR_DIR',
                                'NAME_SRC' : f'{alias}_NME_SRC'},
                                inplace= True) # Rename NGD_STREET fields to match the alias that they are replacing
    print(f'Merging NGD_STREET to NGD_AL for {alias}')
    AL_df = AL_df.merge(aliasStreet, how= 'outer', left_on= f'{alias}_STR_UID_L', right_on= f'{alias}_NGD_STR_UID')
    AL_df.drop(columns= f'{alias}_NGD_STR_UID')
print('Performing full NGD_STREET join with NGD_AL')
NGD_STREET_df = table_to_data_frame(NGD_STREET_tbl)
AL_df = AL_df.merge(NGD_STREET_df, how='outer', left_on='NGD_STR_UID_L', right_on= 'NGD_STR_UID')
del NGD_STREET_df
print('Exporting joins to featureclass')
AL_df.to_featureclass(os.path.join('H:\NGD_AGOL_Download\NGD_Redline.gdb', 'joinPandasTest'), overwrite= True)
print('DONE!')
