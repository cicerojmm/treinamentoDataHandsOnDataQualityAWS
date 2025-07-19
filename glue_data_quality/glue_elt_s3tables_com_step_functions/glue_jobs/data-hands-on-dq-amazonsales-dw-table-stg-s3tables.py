from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg
from awsglue.context import GlueContext
from awsglue.dynamicframe import DynamicFrame
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    IntegerType,
    DoubleType,
)
from awsglue.utils import getResolvedOptions
import sys


def create_spark_session(s3_warehouse_arn):
    return (
      SparkSession.builder.appName("glue-s3-tables-merge")
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
        .config("spark.sql.defaultCatalog", "s3tablesbucket")
        .config("spark.sql.catalog.s3tablesbucket", "org.apache.iceberg.spark.SparkCatalog")
        .config("spark.sql.catalog.s3tablesbucket.catalog-impl", "software.amazon.s3tables.iceberg.S3TablesCatalog")
        .config("spark.sql.catalog.s3tablesbucket.warehouse", s3_warehouse_arn)
        .getOrCreate()
    )



def read_data_csv(spark, file_path):
    df = spark.read.csv(file_path, header=True, inferSchema=True)
    return df


def ensure_namespace_exists(spark: SparkSession, namespace: str):
    spark.sql(f"CREATE NAMESPACE IF NOT EXISTS s3tablesbucket.{namespace}")


def create_table_if_not_exists(spark: SparkSession, namespace: str, table: str, schema: list):
    schema_str = ", ".join([f"{col_name} {col_type}" for col_name, col_type in schema])
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {namespace}.{table} (
            {schema_str}
        )
    """)

def merge_into_table(spark: SparkSession, namespace: str, table: str, primary_key: str, columns: list):
    pk_cols = primary_key.split(",")
    merge_condition = " AND ".join([f"target.{col} = source.{col}" for col in pk_cols])
    set_clause = ", ".join([f"{col} = source.{col}" for col in columns])

    spark.sql(f"""
        MERGE INTO {namespace}.{table} AS target
        USING source_view AS source
        ON {merge_condition}
        WHEN MATCHED THEN UPDATE SET {set_clause}
        WHEN NOT MATCHED THEN INSERT *
    """)


def cast_columns(df):
    return (
        df.withColumn("product_id", col("product_id").cast(StringType()))
        .withColumn("product_name", col("product_name").cast(StringType()))
        .withColumn("category", col("category").cast(StringType()))
        .withColumn("discounted_price", col("discounted_price").cast(DoubleType()))
        .withColumn("actual_price", col("actual_price").cast(DoubleType()))
        .withColumn(
            "discount_percentage", col("discount_percentage").cast(DoubleType())
        )
        .withColumn("rating", col("rating").cast(DoubleType()))
        .withColumn("rating_count", col("rating_count").cast(IntegerType()))
        .withColumn("about_product", col("about_product").cast(StringType()))
        .withColumn("user_id", col("user_id").cast(StringType()))
        .withColumn("user_name", col("user_name").cast(StringType()))
        .withColumn("review_id", col("review_id").cast(StringType()))
        .withColumn("review_title", col("review_title").cast(StringType()))
        .withColumn("review_content", col("review_content").cast(StringType()))
        .withColumn("img_link", col("img_link").cast(StringType()))
        .withColumn("product_link", col("product_link").cast(StringType()))
    )


def main():
    args = getResolvedOptions(sys.argv, [
        'iceberg_table', 
        'primary_key', 
        's3_tables_bucket_arn', 
        'namespace',
        'input_path'
    ])
    
    spark = create_spark_session(args['s3_tables_bucket_arn'])
    df = read_data_csv(spark, args['input_path'])
    df = cast_columns(df)
    df = df.dropDuplicates(['product_id'])
    
    df.createOrReplaceTempView("source_view")

    ensure_namespace_exists(spark, args['namespace'])
    create_table_if_not_exists(spark, args['namespace'], args['iceberg_table'], df.dtypes)
    merge_into_table(spark, args['namespace'], args['iceberg_table'], args['primary_key'], df.columns)


if __name__ == "__main__":
    main()
