import geopandas as gpd
import pandas as pd
from pathlib import Path

# Compare the redline data against NGD_AL and generate SQL statements to be run 
# against NGD so that it reflects those changes.
#
# This is probably a demonstration of the worst use of pandas, so I don't recommend copying it for 
# use anywhere else.

# global constants
TBL_NAME = "NGD.NGD_AL"
UID_FIELD = "NGD_UID"

def get_field_value_for_ngduid(df, field, uid):
    """Get a specific value from a dataframe based on the row ID."""

    subdf = df[df[UID_FIELD] == uid]
    # there is only one record left, so grab the first one
    return subdf.iloc[0][field]

def normalize_value(value):
    """Ensure a value is either a string or an integer."""

    if type(value) is str:
        if len(value):
            return value
    elif type(value) is float and pd.notna(value):
        int(value)
    else:
        return None

if __name__ == '__main__':
    data_dir = Path('..')
    # paths to data files
    redline_path = data_dir.joinpath('redline_ngdal.geojson')
    ngdal_path = data_dir.joinpath('ngdal_affected.geojson')
    # paths to outputs
    ngdal_sql_path = data_dir.joinpath('redline_ngdal_updates.sql')

    # the SQL statements to be written to the output file
    stmts = []
    
    # load the data
    print("Reading data files.")
    redline = gpd.read_file(redline_path)
    ngdal = gpd.read_file(ngdal_path)

    # clean the data a bit
    print("Cleaning redline.")
    redline = redline[redline[UID_FIELD].notnull()]
    redline[UID_FIELD] = redline[UID_FIELD].astype(int)

    # process the most basic fields to see if there are any changes to be made
    print("Processing basic fields.")
    basic_fields = ['SGMNT_SRC', 'STR_CLS_CDE', 'STR_RNK_CDE']
    for index, row in redline.iterrows():
        uid = row[UID_FIELD]

        for fieldname in basic_fields:
            red_val = normalize_value(row[fieldname])
            ngd_val = get_field_value_for_ngduid(ngdal, fieldname, uid)

            # don't bother processing if there is no value in the redline layer
            if red_val and (ngd_val != red_val):
                sql = f"UPDATE {TBL_NAME} SET {fieldname}={red_val} WHERE {UID_FIELD}={uid}"
                stmts.append(sql)

    print(stmts)