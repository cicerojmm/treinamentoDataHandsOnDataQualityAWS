from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg
from awsglue.context import GlueContext
from awsglue.dynamicframe import DynamicFrame
from delta.tables import DeltaTable
from pyspark.sql.functions import col, regexp_replace
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    IntegerType,
    DoubleType,
)


ruleset = """ 
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
        """

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
    spark = create_spark_session()
    df = spark.read.format("delta").load("s3://cjmm-mds-lake-staged/amazonsales_lakehouse/stg_amazonsales")

    df_dim_user = (
        df.select("user_id", "user_name")
        .distinct()
    )

    write_data_parquet_delta(
        spark,
        df_dim_user,
        "s3://cjmm-mds-lake-curated/amazonsales_lakehouse/dim_user",
        "user_id",
    )

    aplicar_regras_dq(df_dim_user, glueContext, "dim_user", ruleset)

if __name__ == "__main__":
    main()
