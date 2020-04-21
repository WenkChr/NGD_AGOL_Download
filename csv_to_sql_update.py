from pathlib import Path
import pandas as pd
import os

# Read a CSV file and convert any values found within to a set of SQL update statements

# where to find the input data
data_dir = Path('..')
input_csv_path = data_dir.joinpath('redline_ngdal_attr_changed.csv')
output_sql_path = data_dir.joinpath(input_csv_path.stem + ".sql")

print(f"Reading CSV data in {input_csv_path}")
print(f"Writing SQL to {output_sql_path}")

# column to use as the key in the updates
key_column = "NGD_UID"

# name of the table to be updated
tbl_name = "NGDp1"

# read the CSV data, checking each column for a value to use in the update statement
# This would probably be easier with the csv module, but it wasn't recognizing NGD_UID values and I 
# didn't feel like debugging it.
df = pd.read_csv(input_csv_path)
df = df.set_index(key_column)

# columns to be used as values
val_cols = [c for c in df.columns if c != key_column]

# iterate each record, preparing an SQL statement for it
print("Generating SQL statements")
sql = []
for index, row in df.iterrows():
    uid = int(index)
    stmt = f"UPDATE {tbl_name} SET "
    notna = row.dropna().to_dict()
    # sometimes there is no change for a given NGD_UID (likely someone was playing), so skip those ones
    if not len(notna):
        continue

    # iterate every column that has a value to include them in the SQL statement
    for k, v in notna.items():
        # try to set any floats to integers
        val = v
        try:
            val = int(val)
        except:
            # not an integer, so encapsulate in quotes
            val = f"'{val}'"
        stmt += f"{k}={val}, "
    stmt += f"WHERE {key_column} = {uid};"

    # the statement is going to have a ', WHERE' in it, so fix that
    stmt = stmt.replace(', WHERE', ' WHERE')
    
    # append this to the set of sql statements to be written out
    # include a newline character to enable writelines() below
    sql.append(stmt + os.linesep)

# write all the SQL statements to a file to be sent to NGD
print("Writing output SQL file")
with output_sql_path.open(mode='w') as outfile:
    outfile.writelines(sql)