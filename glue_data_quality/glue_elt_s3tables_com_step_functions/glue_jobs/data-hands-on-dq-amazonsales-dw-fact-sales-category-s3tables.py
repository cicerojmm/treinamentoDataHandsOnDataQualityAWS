from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from awsglue.utils import getResolvedOptions
import sys

from pyspark.sql.functions import col, regexp_replace, sum as _sum


def get_args():
    return getResolvedOptions(
        sys.argv,
        [
            "stg_table_sales",
            "dim_product_table",
            "dim_user_table",
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


def gerar_sales_amount_por_usuario_categoria(
    spark, stg_table_sales, dim_product_table, dim_user_table
):
    df_dim_product = spark.sql(f"SELECT * FROM {dim_product_table}")
    df_dim_user = spark.sql(f"SELECT * FROM {dim_user_table}")
    df_stg_sales = spark.sql(f"SELECT * FROM {stg_table_sales}")

    df_limpo = df_stg_sales.withColumn(
        "actual_price_clean",
        regexp_replace("actual_price", "[^0-9.]", "").cast("decimal(10,2)"),
    )

    df_result = (
        df_limpo.alias("s")
        .join(df_dim_product.alias("p"), col("s.product_id") == col("p.product_id"))
        .join(df_dim_user.alias("u"), col("s.user_id") == col("u.user_id"))
        .groupBy("u.user_id", "p.category")
        .agg(_sum("actual_price_clean").alias("sales_amount"))
        .select("user_id", "category", "sales_amount")
    )

    return df_result


def main():
    args = get_args()
    spark = create_spark_session(args["s3_tables_bucket_arn"])

    df_result = gerar_sales_amount_por_usuario_categoria(
        spark,
        args["stg_table_sales"],
        args["dim_product_table"],
        args["dim_user_table"],
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
