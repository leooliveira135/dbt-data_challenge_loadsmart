from pyspark.sql import SparkSession

def load_data_challenge(spark: SparkSession, s3_path: str, table_name: str):
    """
    Load CSV data from S3 into a Spark DataFrame and create a temporary view.

    :param spark: SparkSession object
    :param s3_path: S3 path to the CSV files
    :param table_name: Name of the temporary view to create
    """
    # Read CSV data from S3
    df = spark.read.format("csv") \
        .option("header", "true") \
        .option("inferSchema", "true") \
        .load(s3_path)
    
    # Write DataFrame to the glue catalog
    df.write.saveAsTable(table_name, mode="overwrite")

    print(f"Data loaded into temporary view '{table_name}' from '{s3_path}'")

def main(spark: SparkSession):
    # Define S3 path and table name
    s3_path = "s3a://data-challenge-loadsmart-raw/data/"
    table_name = "data_challenge"

    # Load data into Spark
    load_data_challenge(spark, s3_path, table_name)

    # Example query to show data
    result_df = spark.sql(f"SELECT * FROM {table_name} LIMIT 10")
    result_df.show()

if __name__ == "__main__":
    
    spark = SparkSession.builder \
        .appName("Loadsmart Data Challenge") \
        .config(
            "spark.jars.packages",
            "org.apache.hadoop:hadoop-aws:3.3.4,"
            "com.amazonaws:aws-java-sdk-bundle:1.12.262"
        ) \
        .config(
            "spark.hadoop.fs.s3a.aws.credentials.provider",
            "com.amazonaws.auth.profile.ProfileCredentialsProvider"
        ) \
        .config("spark.hadoop.fs.s3a.profile", "default") \
        .getOrCreate()
    
    main(spark)

    spark.stop()