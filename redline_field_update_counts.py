#-------------------------------------------------------------------------------
# Name:        redline_field_update_counts.py
# Purpose:     to count field variables and unique NGD_UID counts in a SQL file and export them to a CSV
#
# Author:      Chris Jobson
#
# Created:     12/05/2020
#-------------------------------------------------------------------------------

import csv, os
from collections import OrderedDict
from dotenv import load_dotenv

# Setup env
load_dotenv(os.path.join(os.getcwd(), 'environments.env'))

sql_file = os.getenv('NGD_ATTR_SQL_PATH')

csv_name = os.getenv('FROM_DATE_TIME').split(' ')[0].replace('-', '_') + '_' + os.getenv('TO_DATE_TIME').split(' ')[0].replace('-', '_')
csv_count_output = os.path.join(os.getenv('NGD_DATA_DIR'), 'redline_count_' + csv_name + '.csv')

field_list = ["AFL_VAL",
"ATL_VAL",
"AFR_VAL",
"ATR_VAL",
"AFL_SRC",
"ATL_SRC",
"AFR_SRC",
"ATR_SRC",
"AFL_DTE",
"ATL_DTE",
"AFR_DTE",
"ATR_DTE",
"ADDR_TYP_L",
"ADDR_TYP_R",
"ADDR_PRTY_L",
"ADDR_PRTY_R",
"NGD_STR_UID_L",
"NGD_STR_UID_R",
"NGD_STR_UID_DTE_L",
"NGD_STR_UID_DTE_R",
"ALIAS1_STR_UID_L",
"ALIAS1_STR_UID_R",
"ALIAS2_STR_UID_L",
"ALIAS2_STR_UID_R",
"EC_STR_ID_L",
"EC_STR_ID_R",
"NAME_SRC_L",
"NAME_SRC_R",
"NGD_UID"
]


def sqlVariableCounts(sql_file, csv_count_output, field_list):
    field_dict = OrderedDict()

    for field in field_list:
        field_dict[field] = 0

    """in case unique ngd counts are requested/can be used as a list
    for this purpose"""
    ngd_dict = {}

    #read SQL file and make dictionaries
    with open(sql_file, "r") as sf:
        lines = sf.readlines()
        for line in lines:
            #just in case
            if "WHERE NGD_UID=" in line:
                ngd_uid = line.split("=")[-1].replace(";", "")
                if ngd_uid not in ngd_dict:
                    ngd_dict[ngd_uid] = 1
                else:
                    ngd_dict[ngd_uid] += 1

            for f in field_dict.keys():
                if f in line:
                    field_dict[f] += 1

    #add unique NGD_UID count to field_dict
    field_dict["NGD_UID"] = len(ngd_dict)

    #create csv from dictionaries
    with open(csv_count_output, 'w') as cf:
        output_fields = ["VARIABLE" ,"COUNT"]
        writer = csv.DictWriter(cf, fieldnames=output_fields)
        writer.writeheader()
        for f, c in field_dict.items():
            writer.writerow({"VARIABLE": f, "COUNT": c})

    print("{} created!".format(csv_count_output))

sqlVariableCounts(sql_file=sql_file, csv_count_output=csv_count_output, field_list=field_list)
