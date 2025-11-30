from botocore.exceptions import ClientError
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, to_timestamp, trim
from src.loader.vars import *
import boto3
import copy
import logging
import time

def load_data_into_bucket(df, path, partition_list):
    """
    Load data into an S3 bucket using Deltalake.
        :param df: DataFrame to be loaded
        :param path: S3 path to load data into
        :param partition_list: List of columns to partition by
    """

    df.write.mode('overwrite').partitionBy(partition_list).parquet(path)
    logging.info(f"Loading the file {path} into the S3 bucket {path.split('/')[2]}")

def read_aws_credentials(profile_name: str):
    """
    Read AWS credentials from a given profile.
        :param profile_name: Name of the AWS profile
        :return: Dictionary containing AWS access key and secret key
    """
    session = boto3.Session(profile_name=profile_name)
    account_id = session.client('sts').get_caller_identity().get('Account')
    return {
        "region_name": session.region_name,
        "account_id": account_id
    }

def load_data_into_glue_database(database_name: str, table_name: str, s3_path: str, account_id: str, crawler_name: str):
    """
    Load data into AWS Glue Data Catalog.
        :param database_name: Name of the Glue database
        :param table_name: Name of the Glue table
        :param s3_path: S3 path where the data is stored
        :param account_id: AWS account ID
        :param crawler_name: Name of the Glue crawler
    """
    glue_client = boto3.client('glue')
    role_arn = f"arn:aws:iam::{account_id}:role/{aws_glue_role}"

    try:
        logging.info(f"Creating Glue crawler '{crawler_name}' for table '{table_name}' in database '{database_name}'")
        glue_client.create_crawler(
            Name=crawler_name,
            Role=role_arn,
            DatabaseName=database_name,
            Targets={
                "S3Targets": [
                    {"Path": s3_path.replace("s3a://", "s3://")},
                ]
            },
            TablePrefix=f"{table_name}_",
        )
        logging.info(f"Crawler '{crawler_name}' created successfully.")

    except ClientError as e:
        logging.error(f"Error creating crawler {crawler_name}: {e}")


def run_glue_crawler(crawler_name: str, table_name: str, database_name: str):
    """
    Start the AWS Glue crawler to update the Data Catalog.
        :param crawler_name: Name of the Glue crawler
        :param table_name: Name of the Glue table
        :param database_name: Name of the Glue database
    """
    glue_client = boto3.client('glue')
    response = glue_client.start_crawler(Name=crawler_name)
    new_table_name = f"{table_name}_athena"

    logging.info(f"Started crawler '{crawler_name}' to update Glue Data Catalog.")
    logging.info(f"Status response: {response}")

    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        logging.error(f"Failed to start crawler '{crawler_name}'.")
        exit(1)

    while True:
        state = glue_client.get_crawler(Name=crawler_name)["Crawler"]["State"]
        logging.info("Crawler state: %s", state)
        if state == "READY":
            break
        time.sleep(5)

    logging.info("Crawler %s finished", crawler_name)
    
    db_list = glue_client.get_tables(DatabaseName=database_name)
    table_list = [table['Name'] for table in db_list['TableList']]
    logging.info(f"Tables in database '{database_name}': {table_list}")

def read_s3_file(spark: SparkSession, s3_path: str, table_name: str):
    """
    Load CSV data from S3 into a Spark DataFrame and create a temporary view.
        :param spark: SparkSession object
        :param s3_path: S3 path to the CSV files
        :param table_name: Name of the temporary view to create
    """
    print(f"Data loaded into temporary view '{table_name}' from '{s3_path}'")

    # Read CSV data from S3
    return spark.read.format("csv") \
        .option("header", "true") \
        .option("inferSchema", "true") \
        .load(s3_path)

def convert_field_to_date(df, field_name: str, date_format: str):
    """
    Convert a field in the DataFrame to date format.
        :param df: Input DataFrame
        :param field_name: Name of the field to convert
        :param date_format: Date format string
        :return: DataFrame with the converted date field
    """
    return df.withColumn(field_name, to_timestamp(trim(col(field_name)), date_format))

def main(spark: SparkSession):
    """
    Main function to load, process, and store data.
        :param spark: SparkSession object
    """
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting data load process...")

    logging.info(f"Reading AWS credentials for profile: {aws_profile_name}")
    creds = read_aws_credentials(aws_profile_name)
    region, account_id = creds["region_name"], creds["account_id"]

    # Load data into Spark
    logging.info(f"Loading data from {input_s3_path} into table {table_name}")
    df = read_s3_file(spark, input_s3_path, table_name)
    df.createOrReplaceTempView(table_name)

    # Example query to show data before processing
    logging.info(f"Querying top 10 records from table {table_name}")
    result_df = spark.sql(f"SELECT * FROM {table_name} LIMIT 10")
    result_df.show()
    logging.info("Schema of the loaded data:")
    result_df.printSchema()

    # Process conversion of date/time fields
    datetime_format = date_format

    transform_df = df
    for field in df.schema.fields:
        is_string = field.dataType.simpleString() == "string"
        name = field.name.lower()

        if is_string and ("date" in name or "time" in name):
            logging.info(f"Converting field '{field.name}' with format {datetime_format}")
            transform_df = convert_field_to_date(transform_df, field.name, datetime_format)

    # Add partitioning column
    transform_df = transform_df.withColumn(partition_key, lit(partition_data).cast("date"))

    # Example query to show data after processing
    logging.info(f"Querying top 20 records after date conversion from table {table_name}")
    transform_df.show()
    logging.info("Schema after date conversion:")
    transform_df.printSchema()

    # Load processed data into S3 as Deltalake
    logging.info(f"Loading processed data into S3 at {output_s3_path}")
    load_data_into_bucket(transform_df, output_s3_path, partition_key)

    # Load data into AWS Glue Data Catalog
    logging.info(f"Loading data into AWS Glue Data Catalog database: {glue_database}, table: {table_name}")
    load_data_into_glue_database(glue_database, table_name, output_s3_path, account_id, glue_crawler_name)
    # Run the Glue crawler to update the Data Catalog
    logging.info(f"Running Glue crawler: {glue_crawler_name}")
    run_glue_crawler(glue_crawler_name, table_name, glue_database)

if __name__ == "__main__":
    
    spark = SparkSession.builder \
        .appName("Loadsmart Data Loader into S3") \
        .config(
            "spark.jars.packages",
            "org.apache.hadoop:hadoop-aws:3.3.4,"
            "com.amazonaws:aws-java-sdk-bundle:1.12.262"
        ) \
        .config(
            "spark.hadoop.fs.s3a.aws.credentials.provider",
            "com.amazonaws.auth.profile.ProfileCredentialsProvider"
        ) \
        .config("spark.hadoop.fs.s3a.profile", aws_profile_name) \
        .config("spark.sql.legacy.timeParserPolicy", "LEGACY") \
        .getOrCreate()
    
    main(spark)

    spark.stop()