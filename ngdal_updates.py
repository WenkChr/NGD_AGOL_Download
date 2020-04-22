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
DATE_FIELD = "EditDate"
DATE_FORMAT_STRING = "%Y-%m-%d"

def get_field_value_for_ngduid(df, field, uid):
    """Get a specific value from a dataframe based on the row ID."""

    subdf = df[df[UID_FIELD] == uid]
    # there is only one record left, so grab the first one
    return subdf.iloc[0][field]

def normalize_value(value):
    """Ensure a value is either a string or an integer."""

    if type(value) is str:
        if len(value):
            return f"'{value}'"
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
    redline[DATE_FIELD] = pd.to_datetime(redline[DATE_FIELD])
    redline['CreationDate'] = pd.to_datetime(redline['CreationDate'])

    # process the fields that set the ATTRBT_DTE field when they change
    target_date_field = 'ATTRBT_DTE'
    print(f"Processing fields that set {target_date_field}.")
    basic_fields = ['SGMNT_SRC', 'STR_CLS_CDE', 'STR_RNK_CDE',
                    'ADDR_TYP_L', 'ADDR_TYP_R', 'ADDR_PRTY_L', 'ADDR_PRTY_R']
    for index, row in redline.iterrows():
        uid = row[UID_FIELD]

        for fieldname in basic_fields:
            red_val = normalize_value(row[fieldname])
            ngd_val = get_field_value_for_ngduid(ngdal, fieldname, uid)
            date_val = row[DATE_FIELD].strftime(DATE_FORMAT_STRING)

            # don't bother processing if there is no value in the redline layer
            if red_val and (ngd_val != red_val):
                sql = f"UPDATE {TBL_NAME} SET {fieldname}={red_val}, {target_date_field}='{date_val}' WHERE {UID_FIELD}={uid}"
                stmts.append(sql)

    # process address values on the NGD_AL
    print(f"Processing address fields.")
    address_fields = ['AFL_VAL', 'AFL_SFX', 'AFL_SRC', 'ATL_VAL', 'ATL_SFX', 'ATL_SRC', 
                    'AFR_VAL', 'AFR_SFX', 'AFR_SRC', 'ATR_VAL', 'ATR_SFX', 'ATR_SRC']
    for index, row in redline.iterrows():
        uid = row[UID_FIELD]

        for fieldname in address_fields:
            red_val = normalize_value(row[fieldname])
            ngd_val = get_field_value_for_ngduid(ngdal, fieldname, uid)
            date_val = row[DATE_FIELD].strftime(DATE_FORMAT_STRING)

            # determine the name of the date field based on the field value being set
            field_parts = fieldname.split('_')
            target_date_field = field_parts[0] + "_DTE"

            # don't bother processing if there is no value in the redline layer
            if red_val and (ngd_val != red_val):
                sql = f"UPDATE {TBL_NAME} SET {fieldname}={red_val}, {target_date_field}='{date_val}' WHERE {UID_FIELD}={uid}"
                stmts.append(sql)
# what about date format?
    print(stmts)