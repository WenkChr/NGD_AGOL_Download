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
output_cols.extend(compare_cols)

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
# changed = (redline[redline[usecols].eq(ngdal[usecols])][usecols]
#         .merge(redline[keep_cols], how='left', left_index=True, right_index=True))
change_mask = redline[compare_cols].ne(ngdal[compare_cols])
changed = redline[output_cols][change_mask]

# split the changed data based on if there is a geometry change
changed_geom = redline[changed['length'].notna()]
changed_attr = changed[changed['length'].isna()]


# changed = redline.merge(ngdal, on=compare_cols, how='outer', suffixes=['', '_'], indicator=True)
# changed = changed.loc[changed['_merge'] == 'left_only', output_cols]

print("Writing changed data to file.")
changed_attr.to_csv("../redline_ngdal_attr_changed.csv")
changed_geom.to_file("../redline_ngdal_geom_changed.geojson", driver='GeoJSON', index=False)

# merge the records together based on NGD_UID
# print("Joining data to perform comparisons.")
# There are potentially multiple redline changes for a single UID, so be sure to join onto redline.
# merged = redline.merge(ngdal, how='left', on='NGD_UID', suffixes=('_redline', '_ngdal'))
# print(merged.columns)

# print(redline.columns)
# print("Spatial compare: ", len(merged))

# redline_mask = redline[compare_cols]
# print(redline_mask.dtypes)
# ngdal_mask = ngdal[compare_cols]
# print(ngdal_mask.dtypes)
# diff_mask = (redline_mask != ngdal_mask) & ~(redline_mask.isnull() & ngdal_mask.isnull())
# redline[compare_cols][diff_mask].merge(redline[['SGMNT_TYP_CDE', 'SGMNT_SRC', 'STR_CLS_CDE', 'STR_RNK_CDE',
#         'NGD_UID','CreationDate','Creator','EditDate','Editor','Comments',
#         'GlobalID']], left_index=True, right_index=True).to_csv("../redline_ngdal_attr_changed2.csv", index=False)