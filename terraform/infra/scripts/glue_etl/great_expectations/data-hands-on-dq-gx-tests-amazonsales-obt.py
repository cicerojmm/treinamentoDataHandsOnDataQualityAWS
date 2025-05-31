from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg
from awsglue.context import GlueContext
from awsglue.dynamicframe import DynamicFrame
from delta.tables import DeltaTable
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    IntegerType,
    DoubleType,
)


def create_spark_session():
    spark = (
        SparkSession.builder.appName("CuratedLayer")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        )
        .getOrCreate()
    )

    return spark


def read_data_csv(spark, file_path):
    df = spark.read.csv(file_path, header=True, inferSchema=True)
    df.createOrReplaceTempView("amazonsales")
    return df


def write_data_parquet_delta(spark, input_df, delta_table_path, primary_key):
    if not DeltaTable.isDeltaTable(spark, delta_table_path):
        input_df.write.format("delta").mode("overwrite").save(delta_table_path)
    else:
        delta_table = DeltaTable.forPath(spark, delta_table_path)

        primary_key_columns = primary_key.split(",")

        merge_condition = " AND ".join(
            [f"target.{col} = source.{col}" for col in primary_key_columns]
        )
        input_df = input_df.dropDuplicates(primary_key_columns)

        (
            delta_table.alias("target")
            .merge(input_df.alias("source"), merge_condition)
            .whenMatchedUpdate(set={c: col(f"source.{c}") for c in input_df.columns})
            .whenNotMatchedInsertAll()
            .execute()
        )


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
    spark = create_spark_session()
    df = read_data_csv(spark, "s3://cjmm-datalake-mds-raw/sales/amazon.csv")
    df = cast_columns(df)

    write_data_parquet_delta(
        spark,
        df,
        "s3://cjmm-datalake-mds-curated/data-hands-on-df-gx-amazon-sales-obt",
        "product_id",
    )


if __name__ == "__main__":
    main()
