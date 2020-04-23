# Compare the redline NGD_AL data against the source data to detect changes

# Changes that get pushed to the geometry changes workflow:
# 1. No NGD_UID (wholly new geometry)
# 2. The geometry has changed by more than 10m
# 3. Right side has different name flag
# All other records will be put into a single output to look for attribute changes

import geopandas as gpd

# how much leeway is there in matching geometries (0.1 == 10m)
GEOM_ROUNDING_FACTOR = 0.1

# paths to input files
redline_path = '../redline_2020-04-21.geojson'
ngdal_path = '../ngdal_affected.geojson'

# paths to output files
redline_attr_changes = '../redline_attr_changes.geojson'
redline_geom_changes = '../redline_geom_chnages.geojson'

# the columns to be used for equality comparisons
compare_cols = ['AFL_VAL', 'AFL_SFX', 'AFL_SRC', 'ATL_VAL', 'ATL_SFX', 'ATL_SRC',
       'AFR_VAL', 'AFR_SFX', 'AFR_SRC', 'ATR_VAL', 'ATR_SFX', 'ATR_SRC',
       'ADDR_TYP_L', 'ADDR_TYP_R', 'ADDR_PRTY_L', 'ADDR_PRTY_R','length']
output_cols = ['SGMNT_TYP_CDE', 'SGMNT_SRC', 'STR_CLS_CDE', 'STR_RNK_CDE',
        'NGD_UID','CreationDate','Creator','EditDate','Editor','Comments',
        'GlobalID']

# load the data to be compared
print("Loading datasets from disk.")
redline = gpd.read_file(redline_path)
ngdal = gpd.read_file(ngdal_path)

# Step 1 - break away any records without an NGD_UID
print("Looking for new geometries.")
geom_change = redline.loc[redline["NGD_UID"].isna()]

attr_change = redline.loc[redline["NGD_UID"].notna()]
attr_change["NGD_UID"] = attr_change["NGD_UID"].astype(int)

print("Geometry changes: ", len(geom_change))
print("Attibute changes: ", len(attr_change))

# Step 2 - look for any geometries that have a >10m change
print("Looking for changed geometries")
attr_change['geom_threshold'] = (attr_change.geometry.length * GEOM_ROUNDING_FACTOR).round(0)
ngdal['length_threshold'] = (ngdal.geometry.length * GEOM_ROUNDING_FACTOR).round(0)

geom_change_detect = attr_change.merge(ngdal[['NGD_UID','length_threshold']], on='NGD_UID')
is_geom_change = geom_change_detect[geom_change_detect['geom_threshold'] != geom_change_detect['length_threshold']]
geom_change_uids = is_geom_change['NGD_UID'].unique().tolist()

# add the geometry changes to the set with no NGD_UID
geom_change = geom_change.append(attr_change[attr_change['NGD_UID'].isin(geom_change_uids)])

# remove any newly identified geometry changes from the attr_change dataframe
attr_change = attr_change[~attr_change['NGD_UID'].isin(geom_change_uids)]

print("Geometry changes: ", len(geom_change))
print("Attibute changes: ", len(attr_change))

# Step 3 - look for any records identified as having a different street name on either side of the arc
print("Looking for right side street name differences")
diff_rh = attr_change[attr_change['STR_RH_DIFF_FLG'] == 1]
geom_change_uids = diff_rh['NGD_UID'].unique().tolist()
# add the geometry changes to the set with no NGD_UID
geom_change = geom_change.append(attr_change[attr_change['NGD_UID'].isin(geom_change_uids)])
# remove any newly identified geometry changes from the attr_change dataframe
attr_change = attr_change[~attr_change['NGD_UID'].isin(geom_change_uids)]

print("Geometry changes: ", len(geom_change))
print("Attibute changes: ", len(attr_change))

# Write the data to disk
print("Writing change results to disk.")
geom_change.to_file("../redline_geom_changes.geojson", driver='GeoJSON')
attr_change.to_file("../redline_attr_changes.geojson", driver='GeoJSON')
