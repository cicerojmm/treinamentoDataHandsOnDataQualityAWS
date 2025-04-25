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

from pyspark.sql.functions import col, regexp_replace, sum as _sum


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



def gerar_sales_amount_por_usuario_categoria(spark, path_dim, path_stg_sales):
    df_dim_product = spark.read.format("delta").load(f"{path_dim}/dim_product")
    df_dim_user = spark.read.format("delta").load(f"{path_dim}/dim_user")
    df_stg_sales = spark.read.format("delta").load(path_stg_sales)
    
    df_limpo = df_stg_sales.withColumn(
        "actual_price_clean",
        regexp_replace("actual_price", "[^0-9.]", "").cast("decimal(10,2)")
    )

    df_result = (
        df_limpo.alias("s")
        .join(df_dim_product.alias("p"), col("s.product_id") == col("p.product_id"))
        .join(df_dim_user.alias("u"), col("s.user_id") == col("u.user_id"))
        .groupBy("u.user_id", "p.category")
        .agg(
            _sum("actual_price_clean").alias("sales_amount")
        )
        .select("user_id", "category", "sales_amount")
    )

    return df_result


def main():
    spark = create_spark_session()
    path_stg_sales = "s3://cjmm-datalake-staged/amazonsales_lakehouse/stg_amazonsales"
    path_data = "s3://cjmm-datalake-curated/amazonsales_lakehouse"

    df_result = gerar_sales_amount_por_usuario_categoria(spark, path_data, path_stg_sales)

    write_data_parquet_delta(
        spark,
        df_result,
        f"{path_data}/fact_sales_category",
        "user_id",
    )


if __name__ == "__main__":
    main()
