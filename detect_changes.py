from collections import Counter
from dotenv import load_dotenv
from arcgis import GIS
from arcgis.features import GeoAccessor, GeoSeriesAccessor
from arcgis.geometry import Geometry, Polyline, lengths
import pandas as pd
from pathlib import Path
import numpy as np
import os, sys
# Compare the redline NGD_AL data against the source data to detect changes
#
# Data processing is split into two paths - geometry changes or attribute changes. These paths represent whether data 
# is sent back to an operator to be input through the NGD Editor tool, or if an SQL script is used to update the 
# values in the NGD.
#
# Changes that get pushed to the geometry changes workflow:
# 1. No NGD_UID (wholly new geometry)
# 2. The geometry has changed by more than 10m
# 3. Right side has different name flag
# 4. CSD_UID L/R values don't match, so street UIDs are handled differently (boundary arcs)
# 5. Birthing a new record on the NGD_STREET table
#
# All other records will be used to look for attribute changes that produce SQL update statements

def sql_normalize_value(value):
    """Ensure a value is either a string or an integer."""

    # nothing to do when the value is None or NaN
    if value is None or pd.isna(value):
        return None

    # if it is a string just send it as is
    if type(value) is str:
        return value

    # probably a number, so force an integer (there are no floats in what we care about)
    try:
        return int(value)
    except:
        pass

    # nothing else worked, just return None
    return None


# load environment to get settings
BASEDIR = os.getcwd()
load_dotenv(os.path.join(BASEDIR, 'environments.env'))
# tracing of the types of changes being applied
change_type = Counter()

# name of the NGD_UID field in the data
ngd_uid_field = os.getenv('NGD_UID_FIELD')

# the SQL statements to be written to the output file
stmts = []
# ending of an SQL statement
END_SQL_STMT = ";" + os.linesep
NGD_TBL_NAME = os.getenv('NGD_TBL_NAME')

# The field to use for determining the date of a change
edit_date_field = os.getenv('NGD_REDLINE_EDIT_DATE_FIELD')
sql_date_format = os.getenv('NGD_DATE_FORMAT_STRING')

# load the data to be compared
print("Loading datasets from disk...")
# paths to data
redline_path = Path(os.getenv('NGD_REDLINE_DATA'))
redline_layer = os.getenv('NGD_REDLINE_LAYER')
ngd_db_path = Path(os.getenv('NGD_NGDAL_DATA'))
ngdal_layer = os.getenv('NGD_NGDAL_LAYER')
ngdstreet_path = Path(os.getenv('NGD_NGDSTREET_DATA'))

print("Reading NGD_AL source data at", ngd_db_path, "from layer", ngdal_layer)
ngdal = pd.DataFrame.spatial.from_featureclass(os.path.join(ngd_db_path.as_posix(), ngdal_layer), sr= '3347')
print("Loaded", len(ngdal), "records.")

# alias UID fields were not included in the original redline layer, so add them on
print("Reading redline data at", redline_path, "from layer", redline_layer)
redline = (pd.DataFrame.spatial.from_featureclass( os.path.join(redline_path.as_posix(), redline_layer), sr= '3347')
          .merge(ngdal[[ngd_uid_field, 'ALIAS1_STR_UID_L', 'ALIAS1_STR_UID_R', 'ALIAS2_STR_UID_L', 'ALIAS2_STR_UID_R']], 
                on=ngd_uid_field, how='left'))
redline['CreationDate'] = pd.to_datetime(redline['CreationDate'], unit='ms')
redline[edit_date_field] = pd.to_datetime(redline[edit_date_field], unit='ms')
print("Loaded", len(redline), "records.")

# make a list of the NGD_UIDs that have changed so that we can filter the NGD_AL to save on memory
# null will end up in this list, but that won't hurt later
print("Filtering NGD_AL to only records found in the redline.")
modified_ngduids = redline[ngd_uid_field].unique().tolist()
ngdal = ngdal.loc[ngdal[ngd_uid_field].isin(modified_ngduids)]
print("NGD_AL total affected records:", len(ngdal))

# With data loaded and filtered down to a manageable set, run new geometry detections

# Step 1 - break away any records without an NGD_UID
print("Looking for new geometries...")
geom_change = redline.loc[redline[ngd_uid_field].isna()].copy()
attr_change = redline.loc[redline[ngd_uid_field].notna()].copy()

# With geometry changes isolated, some cleaning can be applied to the remaining redline data
attr_change[ngd_uid_field] = attr_change[ngd_uid_field].astype(int)
attr_change['CSD_UID_L'] = pd.to_numeric(attr_change['CSD_UID_L'])
attr_change['CSD_UID_R'] = pd.to_numeric(attr_change['CSD_UID_R'])

print("Geometry changes:", len(geom_change))
print("Attibute changes:", len(attr_change))

# Step 2 - look for any geometries that have a >10m change
print("Looking for changed geometries...")
geom_rounding_factor = float(os.getenv('NGD_GEOM_ROUNDING_FACTOR', 0.1))
print("Using length change tolerance of", geom_rounding_factor)

# inefficient way to get the length of each line segment for each data frame
lines = []
for i in range(len(attr_change)):
    path = attr_change.iloc[i]["SHAPE"]
    lines.append(Polyline(path).length)
attr_change['geom'] = lines
attr_change['geom_threshold'] = round((attr_change['geom'] * geom_rounding_factor), 0)

lines2 = []
for i in range(len(ngdal)):
    path = ngdal.iloc[i]["SHAPE"]
    lines2.append(Polyline(path).length)
ngdal['geom'] = lines2
ngdal['length_threshold'] = round((ngdal['geom'] * geom_rounding_factor), 0)

print("Comparing redline vs NGD_AL geometry lengths.")
geom_change_detect = attr_change.merge(ngdal[[ngd_uid_field,'length_threshold']], on=ngd_uid_field)
is_geom_change = geom_change_detect[geom_change_detect['geom_threshold'] != geom_change_detect['length_threshold']]
geom_change_uids = is_geom_change[ngd_uid_field].unique().tolist()

# add the geometry changes to the set with no NGD_UID
geom_change = geom_change.append(attr_change[attr_change[ngd_uid_field].isin(geom_change_uids)])

# remove any newly identified geometry changes from the attr_change dataframe
attr_change = attr_change[~attr_change[ngd_uid_field].isin(geom_change_uids)]

print("Geometry changes:", len(geom_change))
print("Attibute changes:", len(attr_change))

# Step 3 - look for any records identified as having a different street name on either side of the arc
print("Looking for right side street name difference flag...")
diff_rh = attr_change[attr_change['STR_RH_DIFF_FLG'] == 1]
geom_change_uids = diff_rh[ngd_uid_field].unique().tolist()
# add the geometry changes to the set with no NGD_UID
geom_change = geom_change.append(attr_change[attr_change[ngd_uid_field].isin(geom_change_uids)])
# remove any newly identified geometry changes from the attr_change dataframe
attr_change = attr_change[~attr_change[ngd_uid_field].isin(geom_change_uids)]

print("Geometry changes:", len(geom_change))
print("Attibute changes:", len(attr_change))

# Step 4 - look for any mismatched CSD_UID L/R values and send them to new geometry process

print("Looking for CSD boundary arcs...")
csd_mask = attr_change[attr_change['CSD_UID_L'] != attr_change['CSD_UID_R']]
geom_change_uids = csd_mask[ngd_uid_field].unique().tolist()
# add the geometry changes to the set with no NGD_UID
geom_change = geom_change.append(attr_change[attr_change[ngd_uid_field].isin(geom_change_uids)])
# remove any newly identified geometry changes from the attr_change dataframe
attr_change = attr_change[~attr_change[ngd_uid_field].isin(geom_change_uids)]

print("Geometry changes:", len(geom_change))
print("Attibute changes:", len(attr_change))

# Step 5 - look for changes in street names

print("Looking for changes in street names")

print("Reading NGD_STREET data.")
ngdstreet = (pd.read_csv(ngdstreet_path)
            .fillna(-1))
print("Loaded", len(ngdstreet), "records.")

print("Filling NULL values with -1 to enable searching")
attr_change = attr_change.fillna(-1)

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

#pull date for adding as limter to the output SQL strings incase of EC editing. Skips stale records
pull_date_val = os.getenv('TO_DATE_TIME').split(' ')[0]
# iterate through the search criteria, looking for street updates
for searcher in street_name_searchers:
    print("Processing redline based on", searcher['grouper'])
    groups = attr_change.groupby(searcher['grouper'], sort=False)

    for name, group in groups:
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
            if (group[searcher['redline_uid_field']] == street_uid).all():
                change_type['same'] += 1
                continue

            # this is an attribute update
            change_type['update'] += 1
            date_val = group['EditDate'].tolist()[0].strftime(sql_date_format)
            uid = group[ngd_uid_field].tolist()[0]
            sql = f"UPDATE {NGD_TBL_NAME} SET {searcher['ngdal_uid_field']}={street_uid}, {searcher['date_field']}=to_date('{date_val}', 'YYYY-MM-DD') WHERE {ngd_uid_field}={uid} AND {searcher['date_field']} < to_date('{pull_date_val}', 'YYYY-MM-DD')"
            stmts.append(sql + END_SQL_STMT)
            
            # name changes also have a source attribute that needs to be updated
            if searcher['grouper'][1] == 'STR_NME':
                src_side = searcher['grouper'][0][-2:]
                name_source_field = f'NAME_SRC{src_side}'
                name_source_value = group['NAME_SRC'].tolist()[0]
                # If the user left it blank, set to 'NGD'
                if name_source_value == -1:
                    name_source_value = 'NGD'
                sql = f"UPDATE {NGD_TBL_NAME} SET {name_source_field}='{name_source_value}' WHERE {ngd_uid_field}={uid} AND {searcher['date_field']} < to_date('{pull_date_val}', 'YYYY-MM-DD')"
                stmts.append(sql + END_SQL_STMT)
        
             # reset EC name UID attributes to trigger a change on their side
            if searcher['ngdal_uid_field'].startswith('NGD_STR_UID'):
                ec_field_name = searcher['ngdal_uid_field'].replace('NGD_STR_UID', 'EC_STR_ID')
                sql = f"UPDATE {NGD_TBL_NAME} SET {ec_field_name}=-1 WHERE {ngd_uid_field}={uid} {searcher['date_field']} < to_date('{pull_date_val}', 'YYYY-MM-DD')"
                stmts.append(sql + END_SQL_STMT)

        else:
            # this is a new street name so it is added to the new geometries workflow
            change_type['geom'] += 1

            # it is possible for this data to already be in the geometry updates, so don't write it twice
            group_uid = group[ngd_uid_field].unique().tolist()
            existing_geom_changes = geom_change[geom_change[ngd_uid_field].isin(group_uid)]
            if not len(existing_geom_changes):
                geom_change = pd.concat([geom_change, group.replace(-1, np.nan)])
    
    print("Changes:", change_type)
# remove any geometries that were added onto the new geometry workflow
attr_change = attr_change[~attr_change[ngd_uid_field].isin(geom_change[ngd_uid_field].unique().tolist())]
# reset the filler values
attr_change = attr_change.replace(-1, np.nan)

print("Geometry changes:", len(geom_change))
print("Attibute changes:", len(attr_change))

# Step 6 - look for changes to the address range attributes

print("Looking for changes to address range attributes...")

# process the fields that set the ATTRBT_DTE field when they change
target_date_field = 'ATTRBT_DTE'
print(f"Processing fields that set {target_date_field}.")
# 'STR_CLS_CDE', 'STR_RNK_CDE' - fields ignored due to AGOL editor data replication issues
fields = ['SGMNT_SRC', 'ADDR_TYP_L', 'ADDR_TYP_R', 'ADDR_PRTY_L', 'ADDR_PRTY_R']
donotexist = []
for index, row in attr_change.iterrows():
    uid = row[ngd_uid_field]
    if uid not in ngdal[ngd_uid_field].tolist():
        donotexist.append(uid)
        continue
    for fieldname in fields:
        red_val = sql_normalize_value(row[fieldname])
        ngd_val = ngdal[ngdal[ngd_uid_field] == uid].reset_index().at[0, fieldname]
        date_val = row[edit_date_field].strftime(sql_date_format)

        # don't bother processing if there is no value in the redline layer
        if(ngd_val != red_val) and (pd.notna(red_val) | pd.notna(ngd_val)):
            # need to put quotes on string values for the SQL query
            if type(red_val) is str:
                red_val = f"'{red_val}'"
            # -1 values are due to the fillna operation, so set those to NULL
            if red_val == -1 or red_val == None:
                red_val = "NULL"
            
            sql = f"UPDATE {NGD_TBL_NAME} SET {fieldname}={red_val}, {target_date_field}=to_date('{date_val}', 'YYYY-MM-DD') WHERE {ngd_uid_field}={uid} AND {target_date_field} < to_date('{pull_date_val}', 'YYYY-MM-DD')"
            stmts.append(sql + END_SQL_STMT)
            change_type['update'] += 1
        else:
            change_type['same'] += 1
print(f'DO NOT EXIST: {donotexist}')
print("Changes:", change_type)
# process address values on the NGD_AL, which have a date field that matches their name
print(f"Processing address fields.")
fields = ['AFL_VAL', 'AFL_SFX', 'AFL_SRC', 'ATL_VAL', 'ATL_SFX', 'ATL_SRC', 
        'AFR_VAL', 'AFR_SFX', 'AFR_SRC', 'ATR_VAL', 'ATR_SFX', 'ATR_SRC']
donotexist2 = []
for index, row in attr_change.iterrows():
    uid = row[ngd_uid_field]

    for fieldname in fields:
        if uid not in ngdal[ngd_uid_field].tolist():
            donotexist2.append(uid)
            continue
        red_val = sql_normalize_value(row[fieldname])
        ngd_val = ngdal[ngdal[ngd_uid_field] == uid].reset_index().at[0, fieldname]
        date_val = row[edit_date_field].strftime(sql_date_format)

        # determine the name of the date field based on the field value being set
        field_parts = fieldname.split('_')
        target_date_field = field_parts[0] + "_DTE"

        # don't bother processing if there is no value in the redline layer
        if (ngd_val != red_val) and (pd.notna(red_val) | pd.notna(ngd_val)):
            # need to put quotes on string values for the SQL query
            if type(red_val) is str:
                red_val = f"'{red_val}'"

            # -1 values are due to the fillna operation, so set those to NULL
            if red_val == -1 or red_val == None:
                red_val = "NULL"

            sql = f"UPDATE {NGD_TBL_NAME} SET {fieldname}={red_val}, {target_date_field}=to_date('{date_val}', 'YYYY-MM-DD') WHERE {ngd_uid_field}={uid} < to_date('{pull_date_val}', 'YYYY-MM-DD')"
            stmts.append(sql + END_SQL_STMT)
            change_type['update'] += 1
        else:
            change_type['same'] += 1
print(f'DO NOT EXIST2: {donotexist2}')
print("Changes:", change_type)

# write final results to output
print("Writing outputs")
geom_changes_path = Path(os.getenv('NGD_NEW_GEOM_PATH'))
attr_changes_path = Path(os.getenv('NGD_ATTR_SQL_PATH'))

# write SQL file for attribute updates
print("SQL queries:", len(stmts))
with attr_changes_path.open(mode='w') as sqlfile:
    sqlfile.writelines(stmts)

# write featureclass for new geometries
print("Geometry changes:", len(geom_change))

fields = ['OBJECTID', 'GlobalID', 'Shape__Length', 'CreationDate',	'Creator', 'EditDate', 'Editor', 'NGD_UID', 
        'SGMNT_TYP_CDE', 'SGMNT_SRC', 'STR_CLS_CDE', 'STR_RNK_CDE', 'BB_UID_L', 'BB_UID_R',	'BF_UID_L',	'BF_UID_R',	
        'AFL_VAL', 'AFL_SFX', 'AFL_SRC', 'ATL_VAL', 'ATL_SFX', 'ATL_SRC', 'AFR_VAL', 'AFR_SFX', 'AFR_SRC',
        'ATR_VAL', 'ATR_SFX', 'ATR_SRC', 'ADDR_TYP_L', 'ADDR_TYP_R', 'ADDR_PRTY_L', 'ADDR_PRTY_R', 'NGD_STR_UID_L',
        'NGD_STR_UID_R', 'CSD_UID_L', 'CSD_UID_R', 'PLACE_ID_L', 'PLACE_ID_R',
        'PLACE_ID_L_PREV', 'PLACE_ID_R_PREC', 'NAME_SRC_L', 'NAME_SRC_R', 'FED_NUM_L', 'FED_NUM_R', 'STR_NME',	
        'STR_TYP', 'STR_DIR', 'NAME_SRC', 'STR_NME_ALIAS1', 'STR_TYP_ALIAS1', 'STR_DIR_ALIAS1', 'NAME_SRC_ALIAS1',
        'STR_NME_ALIAS2', 'STR_TYP_ALIAS2', 'STR_DIR_ALIAS2', 'NME_SRC_ALIAS2', 'STR_RH_DIFF_FLG', 'Comments',
        'SHAPE','ALIAS1_STR_UID_L',	'ALIAS1_STR_UID_R',	'ALIAS2_STR_UID_L',	'ALIAS2_STR_UID_R',	'geom',	'geom_threshold']

#Removed for causing errors: 'NGD_STR_UID_DTE_L', 'NGD_STR_UID_DTE_R' 

geom_change[fields].spatial.to_featureclass(os.path.join(Path(os.getenv('NGD_NEW_GEOM_PATH'), 'redline_geom')))
                                   
print('DONE!')
