# Compare the redline NGD_AL data against the source data to detect changes

import geopandas as gpd

# paths to files
redline_path = '../redline_ngdal.geojson'
ngdal_path = '../ngdal_affected.geojson'

# the columns to be used for equality comparisons
compare_cols = ['AFL_VAL', 'AFL_SFX', 'AFL_SRC', 'ATL_VAL', 'ATL_SFX', 'ATL_SRC',
       'AFR_VAL', 'AFR_SFX', 'AFR_SRC', 'ATR_VAL', 'ATR_SFX', 'ATR_SRC',
       'ADDR_TYP_L', 'ADDR_TYP_R', 'ADDR_PRTY_L', 'ADDR_PRTY_R','length']
output_cols = ['SGMNT_TYP_CDE', 'SGMNT_SRC', 'STR_CLS_CDE', 'STR_RNK_CDE',
        'NGD_UID','CreationDate','Creator','EditDate','Editor','Comments',
        'GlobalID']

# load the data to be compared
print("Loading datasets from disk.")
redline = (gpd.read_file(redline_path)
        .to_crs("EPSG:3347")
        .drop_duplicates(subset="NGD_UID", keep="last"))
# remove any null values (new geometries)
redline = redline[redline["NGD_UID"].notna()].set_index("NGD_UID", drop=False)
# convert the NGD_UID values to integer
redline["NGD_UID"] = redline["NGD_UID"].astype(int)

ngdal = (gpd.read_file(ngdal_path)
        .set_index("NGD_UID"))

# get the length as a proxy for geometry comparisons
redline['length'] = redline.geometry.length.round(0)
ngdal['length'] = ngdal.geometry.length.round(0)

print("Determining attribute changes.")
change_mask = redline[compare_cols].ne(ngdal[compare_cols])
changed = redline.where(change_mask)
# only mask columns will have a value, so drop anything else that was there and merge it back.
changed = changed[compare_cols]
changed = changed.merge(redline[output_cols], left_index=True, right_index=True)

# split the changed data based on if there is a geometry change
changed_geom = redline[changed['length'].notna()]
changed_attr = changed[changed['length'].isna()]

print("Writing changed data to file.")
changed_attr.to_csv("../redline_ngdal_attr_changed.csv")
changed_geom.to_file("../redline_ngdal_geom_changed.geojson", driver='GeoJSON', index=False)
