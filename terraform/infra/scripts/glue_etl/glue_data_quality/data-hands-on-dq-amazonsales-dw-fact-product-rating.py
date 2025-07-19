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

from pyspark.sql.functions import col, avg, regexp_extract


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


def gerar_dim_product_rating(spark, path_dim, path_stg_sales):
    df_dim_product = spark.read.format("delta").load(f"{path_dim}/dim_product")
    df_dim_rating = spark.read.format("delta").load(f"{path_dim}/dim_rating")
    df_stg_sales = spark.read.format("delta").load(path_stg_sales)

    df_dim_rating_valid = df_dim_rating.withColumn(
        "rating_num",
        regexp_extract("rating", "^[0-9.]+$", 0).cast("double")
    )

    df_result = (
        df_stg_sales.alias("s")
        .join(df_dim_product.alias("p"), col("s.product_id") == col("p.product_id"))
        .join(df_dim_rating_valid.alias("r"), col("r.product_id") == col("p.product_id"))
        .groupBy("p.product_id", "p.product_name")
        .agg(avg("r.rating_num").alias("avg_rating"))
        .select("product_id", "product_name", "avg_rating")  # <- garante que só essas 3 colunas venham
    )


    return df_result



def main():
    spark = create_spark_session()
    path_stg_sales = "s3://cjmm-mds-lake-staged/amazonsales_lakehouse/stg_amazonsales"
    path_data = "s3://cjmm-mds-lake-curated/amazonsales_lakehouse/"

    df_result = gerar_dim_product_rating(spark, path_data, path_stg_sales)

    write_data_parquet_delta(
        spark,
        df_result,
        f"{path_data}/fact_product_rating",
        "product_id",
    )


if __name__ == "__main__":
    main()
