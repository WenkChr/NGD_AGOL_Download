import arcpy, os, sys
from arcgis import GIS
from zipfile import ZipFile

arcpy.env.overwriteOutput = True

#---------------------------------------------------------------------------
#Functions

def upload_data(in_geo_data, outDir, properties_dict):
    # SRC: https://developers.arcgis.com/labs/python/import-data/ 
    simple_name =  os.path.split(in_geo_data)[1]
    inFile = in_geo_data
    if arcpy.Describe(inFile).dataType != 'ShapeFile':
        arcpy.FeatureClassToFeatureClass_conversion(in_geo_data, outDir, simple_name)
        inFile = os.path.join(outDir, simple_name + '.shp')
    zipPath = os.path.join(outDir, simple_name + '.zip')
    with ZipFile(zipPath, 'w') as myzip:
        myzip.write(inFile)
    #login to AGOL using pro credentials
    gis = GIS('pro')
    # Upload the data using input properties and data location
    shp = gis.content.add(properties_dict, data= zipPath)
    #shp.publish()

#---------------------------------------------------------------------------
#Inputs

inFile = 'H:\\automate_AGOL_download\\AGOL_tests.gdb\\RedLine_datetest' 
outDir = 'H:\\automate_AGOL_download'
properties = {
    'title' : 'Redline_datetest',
    'tags' : 'Redline, datetest',
    'type' : 'Shapefile'
}
#---------------------------------------------------------------------------
#Calls
upload_data(inFile, outDir, properties)

print('DONE!')
