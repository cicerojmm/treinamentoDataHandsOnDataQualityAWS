from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg
from awsglue.utils import getResolvedOptions
import sys
from pyspark.sql.functions import col, avg, regexp_extract


def get_args():
    return getResolvedOptions(
        sys.argv,
        [
            "stg_table_sales",
            "dim_product_table",
            "dim_rating_table",
            "output_table",
            "s3_tables_bucket_arn",
            "namespace_destino",
        ],
    )


def create_spark_session(s3_warehouse_arn):
    return (
        SparkSession.builder.appName("glue-s3-tables-merge")
        .config(
            "spark.sql.extensions",
            "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
        )
        .config("spark.sql.defaultCatalog", "s3tablesbucket")
        .config(
            "spark.sql.catalog.s3tablesbucket", "org.apache.iceberg.spark.SparkCatalog"
        )
        .config(
            "spark.sql.catalog.s3tablesbucket.catalog-impl",
            "software.amazon.s3tables.iceberg.S3TablesCatalog",
        )
        .config("spark.sql.catalog.s3tablesbucket.warehouse", s3_warehouse_arn)
        .getOrCreate()
    )


def create_namespace_if_not_exists(spark, namespace):
    spark.sql(f"CREATE NAMESPACE IF NOT EXISTS s3tablesbucket.{namespace}")


def create_output_table_if_not_exists(spark, df, namespace, table_name):
    ddl = ", ".join([f"{c} {t}" for c, t in df.dtypes])
    spark.sql(
        f"""
        CREATE TABLE IF NOT EXISTS {namespace}.{table_name} (
            {ddl}
        )
    """
    )


def write_output_table(spark, df, namespace, table_name):
    df.createOrReplaceTempView("curated_view")
    spark.sql(
        f"""
        INSERT OVERWRITE {namespace}.{table_name}
        SELECT * FROM curated_view
    """
    )


def gerar_fact_product_rating(
    spark, stg_table_sales, dim_product_table, dim_rating_table
):
    df_dim_product = spark.sql(f"SELECT * FROM {dim_product_table}")
    df_dim_rating = spark.sql(f"SELECT * FROM {dim_rating_table}")
    df_stg_sales = spark.sql(f"SELECT * FROM {stg_table_sales}")

    df_dim_rating_valid = df_dim_rating.withColumn(
        "rating_num", regexp_extract("rating", "^[0-9.]+$", 0).cast("double")
    )

    df_result = (
        df_stg_sales.alias("s")
        .join(df_dim_product.alias("p"), col("s.product_id") == col("p.product_id"))
        .join(
            df_dim_rating_valid.alias("r"), col("r.product_id") == col("p.product_id")
        )
        .groupBy("p.product_id", "p.product_name")
        .agg(avg("r.rating_num").alias("avg_rating"))
        .select("product_id", "product_name", "avg_rating")
    )

    return df_result


def main():
    args = get_args()
    spark = create_spark_session(args["s3_tables_bucket_arn"])

    df_result = gerar_fact_product_rating(
        spark,
        args["stg_table_sales"],
        args["dim_product_table"],
        args["dim_rating_table"],
    )

    create_namespace_if_not_exists(spark, args["namespace_destino"])
    create_output_table_if_not_exists(
        spark, df_result, args["namespace_destino"], args["output_table"]
    )
    write_output_table(
        spark, df_result, args["namespace_destino"], args["output_table"]
    )


if __name__ == "__main__":
    main()
