import geopandas as gpd
import numpy as np
import pandas as pd
from pathlib import Path
import os
from collections import Counter

# Compare the redline data against NGD_STREET and generate SQL statements to be run 
# against NGD so that it reflects those changes.
#
# This is probably a demonstration of the worst use of pandas, so I don't recommend copying it for 
# use anywhere else.

# global constants
TBL_NAME = "NGD.NGD_AL"
UID_FIELD = "NGD_UID"
DATE_FIELD = "EditDate"
DATE_FORMAT_STRING = "%Y-%m-%d"
# ending of an SQL statement
END_SQL_STMT = ";" + os.linesep

def get_value_for_field(df, field, uid):
    """Get a specific value from a dataframe based on the row ID."""

    value = df.iloc[0][field]
    # convert NaN values to None
    if pd.isna(value):
        value = None

    return value

def normalize_value(value):
    """Ensure a value is either a string or an integer."""

    # nothing to do when the value is None or NaN
    if value is None or pd.isna(value):
        return None

    # if it is a string, enclose it in quotes
    if type(value) is str:
        return f"'{value}'"

    # probably a number, so force an integer
    try:
        return int(value)
    except:
        pass

    # nothing else worked, just return None
    return None

if __name__ == '__main__':
    data_dir = Path('..')
    # paths to data files
    redline_path = data_dir.joinpath('redline_attr_changes.geojson')
    ngdal_path = data_dir.joinpath('ngdal_affected.geojson')
    ngdstreet_path = data_dir.joinpath('ngd_street.csv')

    # paths to outputs
    geom_changes_path = data_dir.joinpath('redline_ngdstreet_changes.geojson')
    attr_changes_path = data_dir.joinpath('redline_ngdstreet_updates.sql')

    # tracing of the types of changes being applied
    change_type = Counter()
    stmts = []
    birth_sets = []

    # load up the redline and source street data
    print("Reading data files.")
    # the UID fields for aliases are missing from the redline data, so add them based on NGD_AL data
    ngdal = gpd.read_file(ngdal_path)
    redline_street = (gpd.read_file(redline_path)
                    .merge(ngdal[[UID_FIELD, 'ALIAS1_STR_UID_L', 'ALIAS1_STR_UID_R', 'ALIAS2_STR_UID_L', 'ALIAS2_STR_UID_R']], on=UID_FIELD, how='left'))
    ngdstreet = (pd.read_csv(ngdstreet_path)
                .fillna(-1))

    print(f"Loaded {len(redline_street)} redline records.")
    print(f"Loaded {len(ngdstreet)} NGD_STREET records.")

    # fix up the data types
    redline_street['CSD_UID_L'] = pd.to_numeric(redline_street['CSD_UID_L'])
    redline_street['CSD_UID_R'] = pd.to_numeric(redline_street['CSD_UID_R'])
    # Dates are returned from the API as miliseconds since epoch
    redline_street['CreationDate'] = pd.to_datetime(redline_street['CreationDate'], unit='ms')
    redline_street['EditDate'] = pd.to_datetime(redline_street['EditDate'], unit='ms')

    # Fields will often contain empty data, which would make them be skipped when grouping.
    # This is filled with dummy data to allow searching while still avoiding false positives.
    redline_street = redline_street.fillna(-1)

    # searching criteria and which fields to update when change is detected
    street_name_searchers = [
        # left street name
        {'grouper': ['CSD_UID_L','STR_NME','STR_TYP','STR_DIR'],
        'redline_uid_field': 'NGD_STR_UID_L',
        'ngdal_uid_field': 'NGD_STR_UID_L',
        'date_field': 'NGD_STR_UID_DTE_L'},
        # right street name
        {'grouper': ['CSD_UID_R','STR_NME','STR_TYP','STR_DIR'],
        'redline_uid_field': 'NGD_STR_UID_R',
        'ngdal_uid_field': 'NGD_STR_UID_R',
        'date_field': 'NGD_STR_UID_DTE_R'},
        # left alias 1
        {'grouper': ['CSD_UID_L','STR_NME_ALIAS1','STR_TYP_ALIAS1','STR_DIR_ALIAS1'],
        'redline_uid_field': 'ALIAS1_STR_UID_L',
        'ngdal_uid_field': 'ALIAS1_STR_UID_L',
        'date_field': 'ATTRBT_DTE'},
        # right alias 1
        {'grouper': ['CSD_UID_R','STR_NME_ALIAS1','STR_TYP_ALIAS1','STR_DIR_ALIAS1'],
        'redline_uid_field': 'ALIAS1_STR_UID_R',
        'ngdal_uid_field': 'ALIAS1_STR_UID_R',
        'date_field': 'ATTRBT_DTE'},
        # left alias 2
        {'grouper': ['CSD_UID_L','STR_NME_ALIAS2','STR_TYP_ALIAS2','STR_DIR_ALIAS2'],
        'redline_uid_field': 'ALIAS2_STR_UID_L',
        'ngdal_uid_field': 'ALIAS2_STR_UID_L',
        'date_field': 'ATTRBT_DTE'},
        # right alias 2
        {'grouper': ['CSD_UID_R','STR_NME_ALIAS2','STR_TYP_ALIAS2','STR_DIR_ALIAS2'],
        'redline_uid_field': 'ALIAS2_STR_UID_R',
        'ngdal_uid_field': 'ALIAS2_STR_UID_R',
        'date_field': 'ATTRBT_DTE'}
        ]
    
    # iterate through the search criteria, looking for street updates
    for s in street_name_searchers:
        print("Processing redline based on", s['grouper'])
        redline_groups_left = redline_street.groupby(s['grouper'], sort=False)

        for name, group in redline_groups_left:
            # if this is all null values skip it (nulls were filled with -1, remember)
            if (name[1] == -1 and name[2] == -1 and name[3] == -1):
                # this is a null record, don't waste time looking for a match
                continue

            # look for matchs in the NGD_STREET data
            ngd_match = ngdstreet.loc[
                (ngdstreet['CSD_UID'] == name[0]) & 
                (ngdstreet['STR_NME'] == name[1]) & 
                (ngdstreet['STR_TYP'] == name[2]) & 
                (ngdstreet['STR_DIR'] == name[3])]

            if len(ngd_match):
                # found at least one match, so grab the street ID from the first record
                street_uid = ngd_match.reset_index().at[0, 'NGD_STR_UID']

                # If the UIDs already match then this was a no change
                if (group[s['redline_uid_field']] == street_uid).all():
                    change_type['same'] += 1
                    continue

                # this is an attribute update
                change_type['update'] += 1
                date_val = group['EditDate'].tolist()[0].strftime(DATE_FORMAT_STRING)
                uid = group[UID_FIELD].tolist()[0]
                sql = f"UPDATE {TBL_NAME} SET {s['ngdal_uid_field']}={street_uid}, {s['date_field']}='{date_val}' WHERE {UID_FIELD}={uid}"
                stmts.append(sql + END_SQL_STMT)
                # name changes also have a source attribute that needs to be updated
                if s['grouper'][1] == 'STR_NME':
                    src_side = s['grouper'][0][-2:]
                    name_source_field = f'NAME_SRC{src_side}'
                    name_source_value = group['NAME_SRC'].tolist()[0]
                    # If the user left it blank, set to 'NGD'
                    if name_source_value == -1:
                        name_source_value = 'NGD'
                    sql = f"UPDATE {TBL_NAME} SET {name_source_field}='{name_source_value}' WHERE {UID_FIELD}={uid}"
                    stmts.append(sql + END_SQL_STMT)
            else:
                # this is a new street name
                change_type['birth'] += 1
                birth_sets.append(group)

    # write final results to output
    print("Writing outputs")
    print("Changes: ", change_type)

    # write SQL file for attribute updates
    print("Total SQL queries:", len(stmts))
    with attr_changes_path.open(mode='w') as sqlfile:
        sqlfile.writelines(stmts)

    # write GeoJSON for new street births
    # put all the records into a single GeoDataFrame and replace the -1 filler data
    births = (pd.concat(birth_sets)
            .replace(-1, np.nan))
    print("Total new birth records:", len(births))
    births.to_file(geom_changes_path, driver='GeoJSON')