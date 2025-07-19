from pyspark.sql import SparkSession
from awsglue.context import GlueContext
from awsglue.dynamicframe import DynamicFrame
from awsgluedq.transforms import EvaluateDataQuality
from awsglue.transforms import SelectFromCollection
from awsglue.utils import getResolvedOptions
import sys

RULESETS = {
    "fact_product_rating": """
        Rules = [
            ColumnExists "product_id",
            ColumnExists "product_name",
            ColumnExists "avg_rating",
        
            IsComplete "product_id",
            IsComplete "product_name",
            IsComplete "avg_rating",
        
            ColumnDataType "product_id" = "string",
            ColumnDataType "product_name" = "string",
            ColumnDataType "avg_rating" = "float",
        
            RowCount > 0,
            
            CustomSql "SELECT avg_rating FROM primary WHERE avg_rating > 5"
        ]
    """,
    "fact_sales_category": """
        Rules = [
            ColumnExists "user_id",
            ColumnExists "category",
            ColumnExists "sales_amount",
        
            IsComplete "user_id",
            IsComplete "category",
            IsComplete "sales_amount",
        
            ColumnDataType "user_id" = "string",
            ColumnDataType "category" = "string",
            ColumnDataType "sales_amount" = "float",
        
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
        "fact_product_rating": spark.sql(
            f"SELECT * FROM {namespace}.fact_product_rating"
        ),
        "fact_sales_category": spark.sql(
            f"SELECT * FROM {namespace}.fact_product_rating"
        ),
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
