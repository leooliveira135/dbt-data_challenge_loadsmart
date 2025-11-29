from datetime import datetime

aws_profile_name = "default"
aws_glue_role = "athena-glue-dbt-policy"

input_s3_path = "s3a://data-challenge-loadsmart-raw/data/"
table_name = "data_challenge"
output_s3_path = "s3://data-challenge-loadsmart-stg/deltalake/"

partition_key = "loading_date"
partition_data = datetime.now().strftime("%Y-%m-%d")
date_format = "M/d/yyyy H:mm"

glue_database = "loadsmart"
glue_crawler_name = "loadsmart-data-challenge-crawler"