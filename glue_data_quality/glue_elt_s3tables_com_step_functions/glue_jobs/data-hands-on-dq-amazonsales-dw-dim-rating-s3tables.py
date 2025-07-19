from pyspark.sql import SparkSession
from pyspark.sql.functions import regexp_replace
from awsglue.utils import getResolvedOptions
import sys


def get_args():
    return getResolvedOptions(
        sys.argv,
        [
            "stg_table_sales",
            "output_table",
            "s3_tables_bucket_arn",
            "namespace_destino",
        ],
    )


def read_table_stg_sales(spark, stg_table_sales):
    df_stg_sales = spark.sql(f"SELECT * FROM {stg_table_sales}")
    return df_stg_sales


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


def main():
    args = get_args()
    spark = create_spark_session(args["s3_tables_bucket_arn"])
    df_stg_sales = read_table_stg_sales(spark, args["stg_table_sales"])

    df_dim_rating = df_stg_sales.select(
        "user_id",
        "product_id",
        regexp_replace("rating", ",", ".").cast("decimal(3,2)").alias("rating"),
        regexp_replace("rating_count", ",", ".").cast("bigint").alias("rating_count"),
    )

    create_namespace_if_not_exists(spark, args["namespace_destino"])
    create_output_table_if_not_exists(
        spark, df_dim_rating, args["namespace_destino"], args["output_table"]
    )
    write_output_table(
        spark, df_dim_rating, args["namespace_destino"], args["output_table"]
    )


if __name__ == "__main__":
    main()
