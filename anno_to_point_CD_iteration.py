
import arcpy
from datetime import datetime
arcpy.env.overwriteOutput = True
project = r"D:\GIS\Work\ngd_redline\ngd_redline_canada\ngd_redline_canada_3.aprx"
map_name = "Address Labels All Scales"
feature_field = "CSD_UID_L"
feature_extent_buffer = 10
search_query = "PR_L IS NOT NULL"
output_gdb = r"D:\GIS\Work\ngd_redline\ngd_redline_canada\can_anno_pts.gdb" 

#parameters to create CD_UID dictionary
params_uid_dict = {"project": project,
                   "map_name": map_name,
                   "feature_lyr": "ngd_al_2_aux_4K",    #any of the layers will be fine
                   "feature_field": feature_field,
                   "search_query": search_query
                   }

#parameters for creating annotations and points for each scale
params_4k = {"project": project,
             "map_name": map_name,
             "feature_field": feature_field,
             "feature_lyr": "ngd_al_2_aux_4K",
             "conversion_scale": 4514,
             "feature_extent_buffer": feature_extent_buffer,
             "output_gdb": output_gdb,
             "anno_out_suffix": "_anno_4K",
             "final_pt_fc_name": "can_pts_4K"
             }

params_2k = {"project": project,
             "map_name": map_name,
             "feature_field": feature_field,
             "feature_lyr": "ngd_al_2_aux_2K",
             "conversion_scale": 2257,
             "feature_extent_buffer": feature_extent_buffer,
             "output_gdb": output_gdb,
             "anno_out_suffix": "_anno_2K",
             "final_pt_fc_name": "can_pts_2K"
             }

params_1k = {"project": project,
             "map_name": map_name,
             "feature_field": feature_field,
             "feature_lyr": "ngd_al_2_aux_1K",
             "conversion_scale": 1128,
             "feature_extent_buffer": feature_extent_buffer,
             "output_gdb": output_gdb,
             "anno_out_suffix": "_anno_1K",
             "final_pt_fc_name": "can_pts_1K"
             }

"""----------------------------------"""
def createGdb(output_gdb):
    if arcpy.Exists(output_gdb) == False:
        print("{} does not exist. Creating it now...".format(output_gdb))
        out_folder_path = "\\".join(output_gdb.split("\\")[:-1])
        out_name = output_gdb.split("\\")[-1]
        parameters = {"out_folder_path": out_folder_path,
                      "out_name": out_name
                      }
        
        arcpy.CreateFileGDB_management(**parameters)
        
        print("{} created.".format(output_gdb))
    else:
        print("{} exists.".format(output_gdb))

def createCduidDict(project, map_name, feature_lyr, feature_field, search_query):

    aprx = arcpy.mp.ArcGISProject(project)

    m = aprx.listMaps(map_name)[0]

    lyr = m.listLayers(feature_lyr)[0]
    uid_dict = {}
    print("Building CD feature dictionary...")
    rows = arcpy.da.SearchCursor(lyr, [feature_field, "AFL_VAL", \
                                              "ATL_VAL", \
                                              "AFR_VAL", \
                                              "ATR_VAL", "SHAPE@"], search_query)
                                            
    for row in rows:
           
        feature, afl, atl, afr, atr, geom = row

        #in case any null values that can't be parsed happened to have address values... 
        if feature is None:
            feature = 0000
        else:
            feature = feature[:4]

        xmin = geom.extent.XMin
        xmax = geom.extent.XMax
        ymin = geom.extent.YMin
        ymax = geom.extent.YMax

        if feature not in uid_dict:
            uid_dict[feature] = {"XMIN": xmin, "YMIN": ymin, "XMAX": xmax, "YMAX": ymax, \
                                "F_COUNT": 1, "AFL_COUNT": 0, "ATL_COUNT": 0, "AFR_COUNT": 0, "ATR_COUNT": 0}
            
        else:
            uid_dict[feature]["F_COUNT"] += 1
            if xmin < uid_dict[feature]["XMIN"]:
                uid_dict[feature]["XMIN"] = xmin

            if ymin < uid_dict[feature]["YMIN"]:
                uid_dict[feature]["YMIN"] = ymin

            if xmax > uid_dict[feature]["XMAX"]:
                uid_dict[feature]["XMAX"] = xmax

            if ymax > uid_dict[feature]["YMAX"]:
                uid_dict[feature]["YMAX"] = ymax
           
        if afl is not None:
            uid_dict[feature]["AFL_COUNT"] += 1

        if atl is not None:
            uid_dict[feature]["ATL_COUNT"] += 1

        if afr is not None:
            uid_dict[feature]["AFR_COUNT"] += 1
            
        if atr is not None:
            uid_dict[feature]["ATR_COUNT"] += 1

    return uid_dict
    #del lyr
    #del m            
    #del aprx
                                    
def iterateAnnoByCD(project, map_name, feature_lyr, feature_field, conversion_scale, \
                    feature_extent_buffer, output_gdb, anno_out_suffix, \
                    final_pt_fc_name, uid_dict):
    
    arcpy.env.workspace = output_gdb
    arcpy.env.overwriteOutput = True
    anno_pt_list = []
    aprx = arcpy.mp.ArcGISProject(project)

    m = aprx.listMaps(map_name)[0]

    lyr = m.listLayers(feature_lyr)[0]
        

    print("Accessing feature dictionary to create annotations and points...")

    for feature, feature_dict in uid_dict.items():

        f_count = feature_dict["F_COUNT"]
        addr_sum = feature_dict["AFL_COUNT"] + feature_dict["ATL_COUNT"] + feature_dict["AFR_COUNT"]+ feature_dict["ATR_COUNT"]

        xmin = feature_dict["XMIN"]
        ymin = feature_dict["YMIN"]
        xmax = feature_dict["XMAX"]
        ymax = feature_dict["YMAX"]
        
        print("Creating annotations from {}.".format(feature))
        
        xmin = feature_dict["XMIN"]
        ymin = feature_dict["YMIN"]
        xmax = feature_dict["XMAX"]
        ymax = feature_dict["YMAX"]

        feature_extents = "{} {} {} {}".format(xmin - feature_extent_buffer, ymin - feature_extent_buffer,\
                                            xmax + feature_extent_buffer, ymax + feature_extent_buffer)


        print("CD {} address count: {}".format(feature, addr_sum))

        
        anno_output = "{}_{}".format(anno_out_suffix, feature)
        lyr.definitionQuery = "{} LIKE '{}%'".format(feature_field, feature)
        
        if lyr.supports("SHOWLABELS"):
            lyr.showLabels = True
            for label_class in lyr.listLabelClasses():
                if "AFL" in label_class.name or \
                    "ATL" in label_class.name or \
                    "AFR" in label_class.name or \
                    "ATR" in label_class.name:
                    label_class.visible = True
        
        aprx.save()
        anno_name = "{}{}".format(feature_lyr, anno_output)
        print("Creating annotations {} from feature {}".format(anno_name, feature))
        start_time = datetime.now()
        print(start_time)

        #if not using arcgis/google need to update service_file parameter
        #may need to update extent param to the feature extents if possible

        parameters = {"input_map": m,
                    "conversion_scale": conversion_scale,
                    "output_geodatabase": output_gdb,
                    "anno_suffix": anno_output,
                    "extent": feature_extents,
                    "generate_unplaced": "GENERATE_UNPLACED",
                    "feature_linked": "STANDARD",
                    "which_layers": "SINGLE_LAYER",
                    "single_layer": feature_lyr 
                    }
               
        arcpy.cartography.ConvertLabelsToAnnotation(**parameters)

        end_time = datetime.now()
        duration = end_time - start_time
        
        print("{} created in {}.".format(anno_name, duration))


        if final_pt_fc_name is not None and final_pt_fc_name is not "":
            start_time = datetime.now()
            print("Creating points from feature {} annotations".format(feature))
            pt_anno_fc = "pts{}_{}".format(anno_out_suffix, feature)

            parameters = {"in_features": "{}\\{}".format(output_gdb, anno_name),
                          "out_feature_class": "{}\\{}".format(output_gdb, pt_anno_fc),
                          "point_location": "INSIDE"
                          }
            arcpy.FeatureToPoint_management(**parameters)
            end_time = datetime.now()
            duration = end_time - start_time
        
            print("{} created in {}.\n".format(pt_anno_fc, duration))
            anno_pt_list.append("{}\\{}".format(output_gdb, pt_anno_fc))
    print("annoptlist")
    print(anno_pt_list)   
    if final_pt_fc_name is not None and final_pt_fc_name is not "":            
        print("Merging points together to create {}".format(final_pt_fc_name))
        #print(anno_pt_list)
        parameters = {"inputs": anno_pt_list,
                      "output": "{}\\{}".format(output_gdb, final_pt_fc_name)
                      }
        
        arcpy.Merge_management(**parameters)

        print("{} created.\n".format(final_pt_fc_name))
            
    lyr.definitionQuery = ""
    aprx.save()
    del lyr
    del feature_lyr
    del m
    del aprx

createGdb(output_gdb)                                    
uid_dict = createCduidDict(**params_uid_dict)
params_4k["uid_dict"] = uid_dict
params_2k["uid_dict"] = uid_dict
params_1k["uid_dict"] = uid_dict
iterateAnnoByCD(**params_4k)
iterateAnnoByCD(**params_2k)
iterateAnnoByCD(**params_1k)
