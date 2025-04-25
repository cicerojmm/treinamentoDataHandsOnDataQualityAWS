from pyspark.sql import SparkSession
from awsglue.context import GlueContext
from awsglue.dynamicframe import DynamicFrame
from delta.tables import DeltaTable
from awsgluedq.transforms import EvaluateDataQuality
from awsglue.transforms import SelectFromCollection

RULESETS = {
    "fact_product_rating": '''
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
    ''',
    "fact_sales_category": '''
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
    '''
}

def create_spark_session():
    return (
        SparkSession.builder.appName("CuratedLayer")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .getOrCreate()
    )

def ler_dimensoes(spark, path_base):
    return {
        "fact_product_rating": spark.read.format("delta").load(f"{path_base}/fact_product_rating"),
        "fact_sales_category": spark.read.format("delta").load(f"{path_base}/fact_sales_category"),
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
            "resultsS3Prefix": "s3://cjmm-datalake-curated/mds_data_quality_results/glue_dq",
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
    spark = create_spark_session()
    glueContext = GlueContext(spark.sparkContext)
    path_data = "s3://cjmm-datalake-curated/amazonsales_lakehouse"

    tabelas = ler_dimensoes(spark, path_data)

    for nome_tabela, df in tabelas.items():
        print(f"Aplicando regras de qualidade em: {nome_tabela}")
        aplicar_regras_dq(
            df,
            glueContext,
            f"amazonsales_lakehouse_{nome_tabela}",
            RULESETS[nome_tabela]
        )

if __name__ == "__main__":
    main()
