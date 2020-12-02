import os
import sys

import arcpy
import pandas as pd
from arcgis.features import FeatureLayer, GeoAccessor
from arcgis.gis import GIS
from dotenv import load_dotenv

arcpy.env.overwriteOutput = True
# Compare Redline against the NGD_AL and check topology initially for overlaps that make no sense.
# Take the overlaps output into a new QC layer with an issue field tagged in the output

#-------------------------------------------------------------------------------------------------
# Inputs

#url = r'https://services7.arcgis.com/bRi0AN5rG57dCDE4/arcgis/rest/services/NGD_STREET_Redline_V2_61/FeatureServer/0' # URL for AGOL NGD_Redline data
url = r'https://services7.arcgis.com/bRi0AN5rG57dCDE4/arcgis/rest/services/NGD_STREET_Redline_V2_6/FeatureServer/0' # URL for the test NGD_Redline data
workingDirectory = r'H:\NGD_AGOL_Download'
working_gdb = os.path.join(workingDirectory, 'Default.gdb')
working_fds = os.path.join(working_gdb, 'TopoCheck')
downloaded_redline_name = 'NGD_Redline'
#-------------------------------------------------------------------------------------------------
#Logic

#Download the red line
gis = GIS('pro')
print('Logged in as: ' + str(gis.properties.user.username))

if os.path.split(url)[1] != '0': # Ensure URL ends in \0 just an AGOL thing
    data_url = os.path.join(url, '0')

if not arcpy.Exists(working_fds):
    print('Creating working feature dataset')
    arcpy.CreateFeatureDataset_management(working_gdb, 'TopoCheck', spatial_reference= arcpy.SpatialReference('WGS 1984 Web Mercator (auxiliary sphere)'))

#query = "EditDate BETWEEN TIMESTAMP '{}' AND TIMESTAMP '{}'".format(from_date, to_date)
arcpy.FeatureClassToFeatureClass_conversion(url, working_fds, downloaded_redline_name) #, where_clause= query)
redlineToCheck = os.path.join(working_fds, downloaded_redline_name)

if not arcpy.Exists:
    print('Downloaded redline does not exist check code')
    sys.exit()

# Create and add layers to Topology
print('Creating topology and adding layers')
topo = arcpy.CreateTopology_management(working_fds, 'RedlineTopo')

arcpy.AddFeatureClassToTopology_management(topo, redlineToCheck)
# Add rules to topology
print('Adding rules to the topology')
arcpy.AddRuleToTopology_management(topo, rule_type= 'Must Not Overlap (Line)', in_featureclass= redlineToCheck)

print('Validating topology')
arcpy.ValidateTopology_management(topo, 'Full_Extent')

print('Exporting errors from topology')
arcpy.ExportTopologyErrors_management(topo, working_gdb, 'Redline_Topo')

print('DONE!')
