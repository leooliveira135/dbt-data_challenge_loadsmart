from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, to_timestamp, trim
from src.loader.vars import *
from deltalake import write_deltalake
import boto3
import logging

def create_deltalake_storage_options(access_key, secret_key, region_name):
    """
    Create Deltalake storage options for AWS S3 access.
        :param access_key: AWS access key
        :param secret_key: AWS secret key
        :param region_name: AWS region name
        :return: Dictionary of storage options
    """

    logging.info("Deltalake storage options created successfully")
    return {
        "AWS_REGION":region_name,
        'AWS_ACCESS_KEY_ID': access_key,
        'AWS_SECRET_ACCESS_KEY': secret_key,
        'AWS_S3_ALLOW_UNSAFE_RENAME': 'true',
    }

def load_data_into_bucket(path, object_data, storage_options, partition_list):
    """
    Load data into an S3 bucket using Deltalake.
        :param path: S3 path to load data into
        :param object_data: Data to be loaded
        :param storage_options: Storage options for Deltalake
        :param partition_list: List of columns to partition by
    """

    write_deltalake(
        path,
        object_data,
        storage_options=storage_options,
        mode='overwrite',
        partition_by=partition_list
    )
    logging.info(f"Loading the file {path} into the S3 bucket {path.split('/')[2]}")

def read_aws_credentials(profile_name: str):
    """
    Read AWS credentials from a given profile.
        :param profile_name: Name of the AWS profile
        :return: Dictionary containing AWS access key and secret key
    """
    session = boto3.Session(profile_name=profile_name)
    credentials = session.get_credentials().get_frozen_credentials()
    account_id = session.client('sts').get_caller_identity().get('Account')
    return {
        "aws_access_key_id": credentials.access_key,
        "aws_secret_access_key": credentials.secret_key,
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
        glue_client.create_crawler(
            Name=crawler_name,
            Role=role_arn,
            DatabaseName=database_name,
            Targets={
                "S3Targets": [
                    {"Path": s3_path},
                ]
            },
        )
        logging.info(f"Crawler '{crawler_name}' created successfully.")

    except glue_client.exceptions.AlreadyExistsException:
        print(f"Crawler '{table_name}' already exists. Updating crawler definition.")
        glue_client.update_crawler(
            Name=crawler_name,
            Role=role_arn,
            DatabaseName=database_name,
            Targets={
                "S3Targets": [
                    {"Path": s3_path},
                ]
            },
        )
        logging.info(f"Crawler '{crawler_name}' updated successfully.")

    except Exception as e:
        logging.error(f"Error creating/updating crawler: {e}")

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
    access_key, secret_key, region, account_id = creds["aws_access_key_id"], creds["aws_secret_access_key"], creds["region_name"], creds["account_id"]

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

    # Prepare Deltalake storage options
    logging.info("Preparing Deltalake storage options")
    storage_options = create_deltalake_storage_options(access_key, secret_key, region)

    # Load processed data into S3 as Deltalake
    logging.info(f"Loading processed data into S3 at {output_s3_path}")
    load_data_into_bucket(output_s3_path, transform_df.toPandas(), storage_options, [partition_key])

    # Load data into AWS Glue Data Catalog
    logging.info(f"Loading data into AWS Glue Data Catalog database: {glue_database}, table: {table_name}")
    load_data_into_glue_database(glue_database, table_name, output_s3_path, account_id, glue_crawler_name)

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