import os, sys, arcpy, time
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

NGD_STREET_tbl = r'H:\NGD_AGOL_Download\NGD_Redline.gdb\NGD_STREET'
NGD_AL_fc = r'H:\NGD_AGOL_Download\Final_Export_2020-05-29_2.gdb\WC2021NGD_AL_20200313_'
outPath = r'H:\NGD_AGOL_Download'
AL_csv = os.path.join(outPath, 'NGD_AL.csv')
joinedCSV_Name = 'jointest.csv'
chunkSize = 100000
#-------------------------------------------------------------------------------------------------------------------------------------
#Logic
t0 = time.time()
print('Converting NGD_AL data into a csv')
#AL_csv = arcpy.TableToTable_conversion(NGD_AL_fc, r'H:\NGD_AGOL_Download', 'NGD_AL.csv')
count = 0
NGD_STREET_df = table_to_data_frame(NGD_STREET_tbl, ['NGD_STR_UID', 'STR_NME', 'STR_TYP', 'STR_DIR', 'NAME_SRC'])
for chunk in pd.read_csv(AL_csv, chunksize= chunkSize, usecols=['NGD_STR_UID_L', 'ALIAS1_STR_UID_L', 'ALIAS2_STR_UID_L']):
    print(f'Running for section {count} to {count + chunkSize}')
    count += chunkSize
    AL_df = chunk
    print('Doing initial merge of NGD_AL and NGD_STREET')
    AL_df = AL_df.merge(NGD_STREET_df, how='outer', left_on='NGD_STR_UID_L', right_on= 'NGD_STR_UID')
    print('Running alias join loop')
    for alias in ['ALIAS1', 'ALIAS2']:
        print(f'Aliasing {alias} fields')
        print('Loading in NGD_STREET')
        aliasStreet = NGD_STREET_df.copy()
        aliasStreet.rename(columns= {'NGD_STR_UID' : f'{alias}_NGD_STR_UID',
                                    'STR_NME' : f'{alias}_STR_NME', 
                                    'STR_TYP' : f'{alias}_STR_TYP',
                                    'STR_DIR' : f'{alias}_STR_DIR',
                                    'NAME_SRC' : f'{alias}_NME_SRC'},
                                    inplace= True) # Rename NGD_STREET fields to match the alias that they are replacing
        print(f'Merging NGD_STREET to NGD_AL for {alias}')
        AL_df = AL_df.merge(aliasStreet, how= 'outer', left_on= f'{alias}_STR_UID_L', right_on= f'{alias}_NGD_STR_UID')
        AL_df.drop(columns= f'{alias}_NGD_STR_UID', inplace= True)
    print('Exporting joins to output csv')
    AL_df.to_csv(os.path.join(outPath, joinedCSV_Name), mode= 'a', header= True)

print('Joining the joined csv to the NGD_AL FC')    


t1 = time.time()
print(f'Script run time: {round((t1-t0)/60, 2)} min')
print('DONE!')
