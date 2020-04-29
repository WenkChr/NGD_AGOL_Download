# Break a layer apart into either the NGD_AL or NGD_STREET components

import geopandas as gpd
import pandas as pd

# fields used for tracking within AGOL
special_cols = ['GlobalID','CreationDate','Creator','EditDate','Editor', 'Comments']

# columns that belong to NGD_AL, mapped to their standard names
ngdal_col_map = {'WC2021NGD_AL_20200313_NGD_UID': 'NGD_UID',
    'WC2021NGD_AL_20200313_SGMNT_TYP': 'SGMNT_TYP_CDE',
    'WC2021NGD_AL_20200313_SGMNT_SRC': 'SGMNT_SRC',
    'WC2021NGD_AL_20200313_STR_CLS_C': 'STR_CLS_CDE',
    'WC2021NGD_AL_20200313_STR_RNK_C': 'STR_RNK_CDE',
    'WC2021NGD_AL_20200313_AFL_VAL': 'AFL_VAL',
    'WC2021NGD_AL_20200313_AFL_SFX': 'AFL_SFX',
    'WC2021NGD_AL_20200313_AFL_SRC': 'AFL_SRC',
    'WC2021NGD_AL_20200313_ATL_VAL': 'ATL_VAL',
    'WC2021NGD_AL_20200313_ATL_SFX': 'ATL_SFX',
    'WC2021NGD_AL_20200313_ATL_SRC': 'ATL_SRC',
    'WC2021NGD_AL_20200313_AFR_VAL': 'AFR_VAL',
    'WC2021NGD_AL_20200313_AFR_SFX': 'AFR_SFX',
    'WC2021NGD_AL_20200313_AFR_SRC': 'AFR_SRC',
    'WC2021NGD_AL_20200313_ATR_VAL': 'ATR_VAL',
    'WC2021NGD_AL_20200313_ATR_SFX': 'ATR_SFX',
    'WC2021NGD_AL_20200313_ATR_SRC': 'ATR_SRC',
    'WC2021NGD_AL_20200313_ADDR_TYP_': 'ADDR_TYP_L',
    'WC2021NGD_AL_20200313_ADDR_TYP1': 'ADDR_TYP_R',
    'WC2021NGD_AL_20200313_ADDR_PRTY': 'ADDR_PRTY_L',
    'WC2021NGD_AL_20200313_ADDR_PR_1': 'ADDR_PRTY_R'}

# columns that belong to NGD_STREET, mapped to their standard names
ngdstreet_col_map = {'WC2021NGD_STREET_202003_STR_N_1': 'STR_NME',
    'WC2021NGD_STREET_202003_STR_TYP': 'STR_TYP',
    'WC2021NGD_STREET_202003_STR_DIR': 'STR_DIR',
    'WC2021NGD_STREET_202003_NAME_SR': 'NAME_SRC'}
# in the DB these fields form their own records
ngdstreet_extra_cols = ['STR_NME_ALIAS1','STR_TYP_ALIAS1','STR_DIR_ALIAS1','NAME_SRC_ALIAS1',
                        'STR_NME_ALIAS2','STR_TYP_ALIAS2','STR_DIR_ALIAS2','NME_SRC_ALIAS2']

# build the list of columns that will end up on each output
ngdal_cols = []
ngdal_cols.extend(special_cols)
ngdal_cols.append('geometry')
ngdal_cols.extend(ngdal_col_map.keys())

ngdstreet_cols = []
ngdstreet_cols.extend(special_cols)
ngdstreet_cols.extend(ngdstreet_extra_cols)
ngdstreet_cols.extend(ngdstreet_col_map.keys())

# read the redline data
data_path = "../redline_2020-04-17.geojson"
df = gpd.read_file(data_path)

# separate the redline data into its component datasets in EC
print("Writing redline geojson for NGD_AL data.")
ngdal = df[ngdal_cols].rename(columns=ngdal_col_map)
ngdal.to_file("../redline_ngdal.geojson", driver='GeoJSON')

print("Writing redline CSV file for NGD_STREET data.")
ngdstreet = pd.DataFrame(df[ngdstreet_cols]).rename(columns=ngdstreet_col_map)

# should the alias values be stacked to align with the name columns? EC has no alias values.
ngdstreet.to_csv("../redline_ngd_street.csv", index=False)