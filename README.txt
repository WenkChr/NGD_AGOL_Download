
# Detect changes between AGOL and NGD datasets

A set of scripts used to detect differences between the AGOL environment and production NGD data.

## Installing prerequisites

In order to run the scripts, some prerequisites need to be installed. All dependencies are noted in the 
`requirements.txt` file, and can be installed with `pip3 install -r requirements.txt`.

## Detecting Differences

Detecting differences consists of running multiple scripts that do different things.

### Step 1 - Download the redline data

Run the automate_download.py script. You will be prompted to input some information:
- Indicate whether you want all records with NDS_UIDs or all records without NGD_UIDs. This input should be either True or False
Indicating True will mean that the downloader will download all records with NGD_UIDs from AGOL and indicating False will download 
all records without NGD_UIDs from AGOL.

- Indicate the date to begin extracting records from in the format YYYY-MM-DD all inputs should be numeric. For example, 
April 11th, 2020 would be 2020-04-11.

- Indicate the date to end extraction on (inclusive). Date format should be the same as the previous input (YYYY_MM_DD)

The file geodatabase will be created in the directory where the automate_download.py file is located. The primary file to be 
concerned with is the NGD_STREET_Redline all othe files are intermediate and 

### Step 2 - Detect changes

Change detect is done by running the `detect_changes.py` script. The script expects certain environment variables to 
be set so that it knows where to find the data and how to parse it. If you don't want to set environment variables 
manually, you can create a `.env` file with the following contents (adjust for your environment):

```
# Locations of specific data files
NGD_DATA_DIR=/Users/goatsweater/Projects/stc/NGD

# Where to find the original NGD data
NGD_NGDAL_DATA=${NGD_DATA_DIR}/ngd_national.gdb
NGD_NGDAL_LAYER=WC2021NGD_AL_20200313

NGD_NGDSTREET_DATA=${NGD_DATA_DIR}/ngd_street.csv
# NGD_NGDSTREET_LAYER=NGD_STREET

# Where to get redline data that was downloaded
NGD_REDLINE_DATA=${NGD_DATA_DIR}/redline_2020-04-21.geojson
# NGD_REDLINE_LAYER=

# Where to save outputs
NGD_NEW_GEOM_PATH=${NGD_DATA_DIR}/redline_new_geom.geojson
NGD_ATTR_SQL_PATH=${NGD_DATA_DIR}/redline_attr_change.sql

# Date field in the redline that marks when data was modified
NGD_REDLINE_EDIT_DATE_FIELD='EditDate'

# Rounding factor to flag new geometries (0.1 = 10m)
NGD_GEOM_ROUNDING_FACTOR=0.1

# Names for SQL queries
NGD_TBL_NAME=NGD.NGD_AL
NGD_UID_FIELD=NGD_UID
NGD_DATE_FORMAT_STRING=%Y-%m-%d
```

For ease of use, the file can be created in the same directory as `detect_changes.py`.

The script takes no arguments, so just call python to run it: `python3 detect_changes.py`. It will look at the 
environment variables to determine how to access NGD and redline data. 

Output files are created based on the values set in the environment, and will consist of a GeoJSON file representing 
data that is to be processed through the NGD editor and an SQL file that can be applied directly to the NGD.

### Step 3 - Upload GeoJSON to AGOL

The GeoJSON file is added back to the AGOL environment to allow NGD editors to load it into their desktop environment 
as a reference layer.