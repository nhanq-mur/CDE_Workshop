#
#Copyright (c) 2020 Cloudera, Inc. All rights reserved.
#

from pyspark.sql import SparkSession
from pyspark.sql.functions import split, regexp_extract, regexp_replace, col
import sys

### Get the username from argument
try:
    username = sys.argv[1].replace('"', '')
    print("...............................")
    print(f"username is : {username}")
except:
    print("........ERROR.......................")
    print("YOU HAVE NOT PASSED THE USERNAME IN THE ARGUMENT SECTION \n PLEASE MODIFY THE JOB CONFIG TO UPDATE THE USERNAME FIELD")

#### Set DB Name and App Name accordingly
db_name = username + "_retail"    ## example: retail_wuser1
appName = username + "-CDE-Lab3-Job1-PySpark-Tokenize"

### Update the username and dbname
# username = "<ENTER YOUR USERNAME HERE" ## example: wuser1
# db_name = "<ENTER YOUR DB NAME HERE>"    ## example: retail_wuser1
# appName = "CDE-Lab3-Job1-PySpark-Tokenize" + username

spark = SparkSession \
    .builder \
    .appName(appName) \
    .getOrCreate()

### Update the s3 details here
input_path ="s3a://pse-workshop/cde-workshop"

base_df=spark.read.text(input_path + "/access-log.txt")

split_df = base_df.select(regexp_extract('value', r'([^ ]*)', 1).alias('ip'),
                          regexp_extract('value', r'(\d\d\/\w{3}\/\d{4}:\d{2}:\d{2}:\d{2} -\d{4})', 1).alias('date'),
                          regexp_extract('value', r'^(?:[^ ]*\ ){6}([^ ]*)', 1).alias('url'),
                          regexp_extract('value', r'(?<=product\/).*?(?=\s|\/)', 0).alias('productstring')
                         )

filtered_products_df = split_df.filter("productstring != ''")
cleansed_products_df=filtered_products_df.select(regexp_replace("productstring", "%20", " ").alias('product'), "ip", "date", "url")

print("...............................")
print("Cleansed product sample:")
print(cleansed_products_df.take(1))

print("...............................")
print(f"Creating {db_name} Database \n")
spark.sql(f"CREATE DATABASE IF NOT EXISTS {db_name}")
print("...............................")
print(f"Inserting Data into {db_name}.tokenized_accesss_logs table \n")

cleansed_products_df.\
  write.\
  mode("overwrite").\
  saveAsTable(db_name+'.'+"tokenized_access_logs", format="parquet")

print(f"Count number of records inserted \n")
spark.sql(f"Select count(*) as RecordCount from {db_name}.tokenized_access_logs").show()

print(f"Retrieve 15 records for validation \n")
spark.sql(f"Select * from {db_name}.tokenized_access_logs limit 15").show()
