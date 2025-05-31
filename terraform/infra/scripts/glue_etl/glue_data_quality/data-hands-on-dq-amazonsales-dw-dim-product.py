from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg
from awsglue.context import GlueContext
from awsglue.dynamicframe import DynamicFrame
from delta.tables import DeltaTable
from pyspark.sql.functions import col
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



def main():
    spark = create_spark_session()
    df = spark.read.format("delta").load("s3://cjmm-datalake-mds-staged/amazonsales_lakehouse/stg_amazonsales")

    df_dim_product = (
        df.select(
            "product_id",
            "product_name",
            "category",
            "about_product",
            "img_link",
            "product_link"
        )
        .distinct()
    )


    write_data_parquet_delta(
        spark,
        df_dim_product,
        "s3://cjmm-datalake-mds-curated/amazonsales_lakehouse/dim_product",
        "product_id",
    )


if __name__ == "__main__":
    main()
