from pyspark.sql import SparkSession
from awsglue.context import GlueContext
from awsglue.dynamicframe import DynamicFrame
from awsgluedq.transforms import EvaluateDataQuality
from awsglue.transforms import SelectFromCollection
from awsglue.utils import getResolvedOptions
import sys

RULESETS = {
    "dim_user": """
        Rules = [
            ColumnExists "user_id",
            ColumnExists "user_name",
            IsComplete "user_id",
            IsComplete "user_name",
            Uniqueness "user_id" > 0.99,
            RowCount > 0,
            ColumnDataType "user_id" = "int",
            ColumnDataType "user_name" = "string"
        ]
    """,
    "dim_product": """
        Rules = [
            ColumnExists "product_id",
            ColumnExists "product_name",
            ColumnExists "category",
            ColumnExists "about_product",
            ColumnExists "img_link",
            ColumnExists "product_link",
            IsComplete "product_id",
            IsComplete "product_name",
            IsComplete "category",
            IsComplete "img_link",
            IsComplete "product_link",
            Uniqueness "product_id" > 0.99,
            ColumnDataType "product_id" = "string",
            ColumnDataType "product_name" = "string",
            ColumnDataType "category" = "string",
            ColumnDataType "about_product" = "string",
            ColumnDataType "img_link" = "string",
            ColumnDataType "product_link" = "string"
        ]
    """,
    "dim_rating": """
        Rules = [
            ColumnExists "user_id",
            ColumnExists "product_id",
            ColumnExists "rating",
            ColumnExists "rating_count",
            IsComplete "user_id",
            IsComplete "product_id",
            IsComplete "rating",
            IsComplete "rating_count",
            ColumnDataType "user_id" = "string",
            ColumnDataType "product_id" = "string",
            ColumnDataType "rating" = "float",
            ColumnDataType "rating_count" = "int",
            RowCount > 0
        ]
    """,
}


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


def ler_dimensoes(spark, namespace):
    return {
        "dim_user": spark.sql(f"SELECT * FROM {namespace}.dim_user"),
        "dim_product": spark.sql(f"SELECT * FROM {namespace}.dim_product"),
        "dim_rating": spark.sql(f"SELECT * FROM {namespace}.dim_rating"),
    }


def aplicar_regras_dq(df, glueContext, nome_contexto, ruleset):
    df_dq = DynamicFrame.fromDF(df, glueContext, nome_contexto)

    dqResultsEvaluator = EvaluateDataQuality().process_rows(
        frame=df_dq,
        ruleset=ruleset,
        publishing_options={
            "dataQualityEvaluationContext": nome_contexto,
            "enableDataQualityCloudWatchMetrics": True,
            "enableDataQualityResultsPublishing": True,
            "resultsS3Prefix": "s3://cjmm-mds-lake-curated/mds_data_quality_results/glue_dq",
        },
        additional_options={"performanceTuning.caching": "CACHE_NOTHING"},
    )

    ruleOutcomes = SelectFromCollection.apply(
        dfc=dqResultsEvaluator,
        key="ruleOutcomes",
        transformation_ctx="ruleOutcomes",
    )

    dqResults = ruleOutcomes.toDF()

    print(dqResults.printSchema())
    dqResults.show(truncate=False)


def main():
    args = getResolvedOptions(
        sys.argv,
        [
            "s3_tables_bucket_arn",
            "namespace",
        ],
    )

    spark = create_spark_session(args["s3_tables_bucket_arn"])
    glueContext = GlueContext(spark.sparkContext)

    tabelas = ler_dimensoes(spark, args["namespace"])

    for nome_tabela, df in tabelas.items():
        print(f"Aplicando regras de qualidade em: {nome_tabela}")
        aplicar_regras_dq(
            df,
            glueContext,
            f"amazonsales_lakehouse_{nome_tabela}",
            RULESETS[nome_tabela],
        )


if __name__ == "__main__":
    main()
