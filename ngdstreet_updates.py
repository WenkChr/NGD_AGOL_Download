import geopandas as gpd
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

    # tracing of the types of changes being applied
    change_type = Counter()
    stmts = []
    birth_sets = []

    # load up the redline and source street data
    print("Reading data files.")
    redline_street = gpd.read_file(redline_path)
    ngdstreet = pd.read_csv(ngdstreet_path).fillna(-1)

    print(f"Loaded {len(redline_street)} redline records.")
    print(f"Loaded {len(ngdstreet)} NGD_STREET records.")

    # fix up the data types
    redline_street['CSD_UID_L'] = pd.to_numeric(redline_street['CSD_UID_L'])
    redline_street['CSD_UID_R'] = pd.to_numeric(redline_street['CSD_UID_R'])
    # Dates are returned from the API as miliseconds since epoch
    redline_street['CreationDate'] = pd.to_datetime(redline_street['CreationDate'], unit='ms')
    redline_street['EditDate'] = pd.to_datetime(redline_street['EditDate'], unit='ms')

    # print(redline_street[['CSD_UID_L','STR_NME','STR_TYP','STR_DIR']].dtypes)
    # print(ngdstreet.dtypes)

    # create groupings based on street data to enable quick lookups
    # print("Grouping NGD_STREET for quick lookups")
    # ngdstreet_groups = ngdstreet.groupby(['CSD_UID','STR_NME','STR_TYP','STR_DIR'])

    # Fields will often contain empty data, which would make them be skipped when grouping.
    # This is filled with dummy data to allow searching while still avoiding false positives.
    redline_street = redline_street.fillna(-1)

    # Fields to update: NGD_STR_UID_L, ALIAS1_STR_UID_L, ALIAS2_STR_UID_L + _R
    # Fields to search: STR_NME_ALIAS1, STR_TYP_ALIAS1, STR_DIR_ALIAS1 + 2
    searchers = [
        # left street name
        {'grouper': ['CSD_UID_L','STR_NME','STR_TYP','STR_DIR'],
        'str_uid_field': 'NGD_STR_UID_L',
        'date_field': 'NGD_STR_UID_DTE_L'},
        # right street name
        {'grouper': ['CSD_UID_R','STR_NME','STR_TYP','STR_DIR'],
        'str_uid_field': 'NGD_STR_UID_R',
        'date_field': 'NGD_STR_UID_DTE_R'},

        # There is no alias ID field - what to do?
        # # left alias 1
        # {'grouper': ['CSD_UID_L','STR_NME_ALIAS1','STR_TYP_ALIAS1','STR_DIR_ALIAS1'],
        # 'str_uid_field': 'ALIAS1_STR_UID_L',
        # 'redline_uid_field': 'NGD_STR_UID_L',
        # 'date_field': None},
        # # right alias 1
        # {'grouper': ['CSD_UID_R','STR_NME_ALIAS1','STR_TYP_ALIAS1','STR_DIR_ALIAS1'],
        # 'str_uid_field': 'ALIAS1_STR_UID_R',
        # 'date_field': None}
        ]
    
    # iterate through the search criteria, looking for street updates
    for s in searchers:
        print("Processing redline based on", s['grouper'])
        redline_groups_left = redline_street.groupby(s['grouper'], sort=False)

        for name, group in redline_groups_left:
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
                if (group[s['str_uid_field']] == street_uid).all():
                    change_type['same'] += 1
                    continue

                # this is an attribute update
                change_type['update'] += 1
                date_val = group['EditDate'].tolist()[0].strftime(DATE_FORMAT_STRING)
                uid = group[UID_FIELD].tolist()[0]
                if s['date_field']:
                    sql = f"UPDATE {TBL_NAME} SET {s['str_uid_field']}={street_uid}, {s['date_field']}='{date_val}' WHERE {UID_FIELD}={uid}"
                else:
                    sql = f"UPDATE {TBL_NAME} SET {s['str_uid_field']}={street_uid} WHERE {UID_FIELD}={uid}"
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

    # write GeoJSON for new street births
    births = pd.concat(birth_sets)
    print("Total new birth records:", len(births))