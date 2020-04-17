# -*- coding: utf-8 -*-

import os, sys, arcpy
from arcgis.gis import GIS

arcpy.env.overwriteOutput = True

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Toolbox"
        self.alias = ""

        # List of tool classes associated with this toolbox
        self.tools = [Tool]


class Tool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "NGD_Redline_Download_Filter"
        self.description = "Downloads the NGD_Redline data from AGOL and filters it for new or old geometry"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        
        AGOL_url = arcpy.Parameter(
            name = 'AGOL_url',
            displayName = 'AGOL data url',
            datatype = 'GPString',
            direction = 'Input',
            parameterType = 'Required')
        
        outGDB = arcpy.Parameter(
            name =  'outGDB',
            displayName = 'output geodatabase',
            datatype = 'DEWorkspace',
            direction = 'Input',
            parameterType = 'Required')
        
        outFileName = arcpy.Parameter(
            name = 'outFileName',
            displayName = 'Out FeatureClass Name',
            datatype = 'GPString',
            direction = 'Input',
            parameterType = 'Required')

        NGD_UID_y_n = arcpy.Parameter(
            name = 'NGD_UID_y_n',
            displayName = 'Features with a NGD_UID',
            datatype = 'GPBoolean',
            direction = 'Input',
            parameterType = 'Required')

        field_prefix = arcpy.Parameter(
            name = 'field_prefix',
            displayName = 'Field Name Prefix',
            datatype = 'GPString',
            direction = 'Input',
            parameterType = 'Required')
        
        AGOL_url.value = r'https://services7.arcgis.com/bRi0AN5rG57dCDE4/arcgis/rest/services/NGD_STREET_Redline/FeatureServer'
        outFileName.value = 'NGD_STREET_Redline'
        NGD_UID_y_n.value = True
        field_prefix.value = 'WC2021NGD_AL_20200313_'
        params = [AGOL_url, outGDB, outFileName, NGD_UID_y_n, field_prefix]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        def auto_download_data(data_url, outGDB, outname, att_or_geo, fieldPrefix= 'WC2021NGD_AL_20200313_'):
            """ Requires you to be logged into arcgis pro on this computer with an account that has access to the data you are trying to 
            download. You must be logged into arcGIS pro with your statscan AGOL account in order for this to work. This funtion will
            go into the NGD group via the arcGIS portal and download a specific feature layer as determined by the file_name variable"""
            #Verify credentials
            gis = GIS('pro')
            arcpy.AddMessage('Logged in as: ' + str(gis.properties.user.username))
            
            if os.path.split(data_url)[1] != '0':
                data_url = os.path.join(data_url, '0')
            
            if att_or_geo:
                arcpy.FeatureClassToFeatureClass_conversion(data_url, outGDB, outname, where_clause= fieldPrefix + "NGD_UID IS NOT NULL")
            if not att_or_geo:
                arcpy.FeatureClassToFeatureClass_conversion(data_url, outGDB, outname, where_clause= fieldPrefix + "NGD_UID IS NULL")
            return os.path.join(outGDB, outname)

        def unique_values(fc, field):
            # Returns a list off unique values for a given field in the unput dataset
            with arcpy.da.SearchCursor(fc, field_names= [field]) as cursor:
                return sorted({row[0] for row in cursor})

        def filter_data_remove_duplicates(Redline_data, outGDB, outName, field_prefix= 'WC2021NGD_AL_20200313_'):
            # Start by finding the most recent date for each NGD_UID and keeping only that date
            KeepRows = []
            for uid in unique_values(Redline_data, field_prefix + 'NGD_UID'):
                fieldnames = [field_prefix + 'NGD_UID', 'EditDate']
                fl = arcpy.MakeFeatureLayer_management(Redline_data, 'fl', where_clause= fieldnames[0] + '= ' + str(uid))
                max_date = max(unique_values(fl, fieldnames[1]))
                with arcpy.da.SearchCursor(fl, field_names= ['OBJECTID', fieldnames[1]]) as cursor:
                    for row in cursor:
                        if row[1] == max_date:
                            KeepRows.append(row[0])
            fl = arcpy.MakeFeatureLayer_management(Redline_data, 'fl2')
            for oid in KeepRows:
                arcpy.SelectLayerByAttribute_management(fl, 'ADD_TO_SELECTION', "OBJECTID = {}".format(oid))
            arcpy.FeatureClassToFeatureClass_conversion(fl, outGDB, outName + '_uniques')
            arcpy.Delete_management(Redline_data)
            return os.path.join(outGDB, outName)    
        
        arcpy.AddMessage('Downloading NGD_AL Redline data from AGOL')
        
        fc = auto_download_data(parameters[0].valueAsText, 
                            parameters[1].valueAsText, 
                            parameters[2].valueAsText, 
                            parameters[3].valueAsText)
        
        arcpy.AddMessage('Filtering downloaded data')
        
        filtered = filter_data_remove_duplicates(fc, 
                            parameters[1].valueAsText, 
                            parameters[2].valueAsText, 
                            field_prefix= parameters[4].valueAsText)
        

        arcpy.AddMessage('DONE!')
        return
