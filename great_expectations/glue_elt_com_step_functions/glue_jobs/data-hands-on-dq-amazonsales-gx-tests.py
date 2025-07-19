import great_expectations as ge
from great_expectations.core import ExpectationSuite
from great_expectations.core.batch import RuntimeBatchRequest
from great_expectations.core.yaml_handler import YAMLHandler
from great_expectations.validator.validator import Validator
from great_expectations.data_context.types.base import DataContextConfig
from great_expectations.profile.basic_dataset_profiler import BasicDatasetProfiler
from great_expectations.dataset.sparkdf_dataset import SparkDFDataset
from os.path import join
from pyspark.context import SparkContext
from pyspark.sql import SparkSession
from awsglue.context import GlueContext
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    BooleanType,
    IntegerType,
    DoubleType,
)

yaml = YAMLHandler()

datasource_yaml = f"""
    name: my_spark_datasource
    class_name: Datasource
    module_name: great_expectations.datasource
    execution_engine:
        module_name: great_expectations.execution_engine
        class_name: SparkDFExecutionEngine
    data_connectors:
        my_runtime_data_connector:
            class_name: RuntimeDataConnector
            batch_identifiers:
                - some_key_maybe_pipeline_stage
                - some_other_key_maybe_airflow_run_id
    """

suite_name = "suite_tests_amazon_sales_data"
suite_profile_name = "profile_amazon_sales_data"


def config_data_docs_site(context, output_path):
    data_context_config = DataContextConfig()

    data_context_config["data_docs_sites"] = {
        "s3_site": {
            "class_name": "SiteBuilder",
            "store_backend": {
                "class_name": "TupleS3StoreBackend",
                "bucket": output_path.replace("s3://", ""),
            },
            "site_index_builder": {"class_name": "DefaultSiteIndexBuilder"},
        }
    }

    context._project_config["data_docs_sites"] = data_context_config["data_docs_sites"]


def create_context_ge(output_path):
    context = ge.get_context()

    context.add_expectation_suite(expectation_suite_name=suite_name)

    context.add_datasource(**yaml.load(datasource_yaml))
    config_data_docs_site(context, output_path)

    return context


def create_validator(context, suite, df):
    runtime_batch_request = RuntimeBatchRequest(
        datasource_name="my_spark_datasource",
        data_connector_name="my_runtime_data_connector",
        data_asset_name="insert_your_data_asset_name_here",
        runtime_parameters={"batch_data": df},
        batch_identifiers={
            "some_key_maybe_pipeline_stage": "ingestion step 1",
            "some_other_key_maybe_airflow_run_id": "run 18",
        },
    )

    df_validator: Validator = context.get_validator(
        batch_request=runtime_batch_request, expectation_suite=suite
    )

    return df_validator


def add_tests_suite(df_validator):
    columns_list = [
        "product_id",
        "product_name",
        "category",
        "discounted_price",
        "actual_price",
        "discount_percentage",
        "rating",
        "rating_count",
        "about_product",
        "user_id",
        "user_name",
        "review_id",
        "review_title",
        "review_content",
        "img_link",
        "product_link",
    ]

    # Validação da estrutura da tabela
    df_validator.expect_table_columns_to_match_ordered_list(columns_list)

    # Unicidade e não-nulos para chaves
    df_validator.expect_column_values_to_be_unique("product_id")
    df_validator.expect_column_values_to_not_be_null("product_id")

    # Valores entre faixas esperadas
    df_validator.expect_column_values_to_be_between(
        "discount_percentage", min_value=0, max_value=100
    )
    df_validator.expect_column_values_to_be_between("rating", min_value=0, max_value=5)
    df_validator.expect_column_values_to_be_between("actual_price", min_value=0.01)
    df_validator.expect_column_values_to_be_between("discounted_price", min_value=0.01)
    df_validator.expect_column_values_to_be_between("rating_count", min_value=0)

    # Tipo esperado para rating_count
    df_validator.expect_column_values_to_be_of_type("rating_count", "IntegerType")

    # Formato esperado para links
    df_validator.expect_column_values_to_match_regex(
        column="product_link",
        regex=r"^https:\/\/www\.[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}$",
        mostly=0.9,
    )

    df_validator.expect_column_values_to_match_regex(
        column="img_link", regex=r"^https:\/\/.*\.(jpg|jpeg|png|webp)$"
    )

    # Formato esperado para IDs
    df_validator.expect_column_values_to_match_regex("review_id", r"^[a-zA-Z0-9_-]+$")
    df_validator.expect_column_values_to_match_regex("user_id", r"^[a-zA-Z0-9_-]+$")
    df_validator.expect_column_values_to_match_regex("product_id", r"^[a-zA-Z0-9_-]+$")

    # Tamanho de textos
    df_validator.expect_column_value_lengths_to_be_between(
        "review_title", min_value=3, max_value=100
    )

    # Cardinalidade composta
    df_validator.expect_compound_columns_to_be_unique(["product_id", "product_name"])

    return df_validator


def add_profile_suite(context, df_ge):
    profiler = BasicDatasetProfiler()
    expectation_suite, validation_result = profiler.profile(df_ge)
    context.save_expectation_suite(expectation_suite, suite_profile_name)


def create_spark_session(app_name="spark-app"):
    return (
        SparkSession.builder.appName("CuratedLayer")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        )
        .getOrCreate()
    )


def read_data(spark, file_path):
    df = spark.read.format("delta").load(file_path)
    df.createOrReplaceTempView("amazonsales")
    return df


def process_results_gx(spark, gx_result):
    # Extração dos dados do resultado
    run_name = gx_result["run_id"]["run_name"]
    result_data = list(gx_result["run_results"].values())[0]["validation_result"]

    validation_time = result_data["meta"]["validation_time"]
    batch_info = result_data["meta"]["active_batch_definition"]
    expectation_results = result_data["results"]
    success_percent = result_data["statistics"]["success_percent"]

    # Criação da lista de dicionários
    rows = [
        {
            "run_name": run_name,
            "validation_time": validation_time,
            "data_asset_name": batch_info["data_asset_name"],
            "expectation_type": e["expectation_config"]["expectation_type"],
            "column": e["expectation_config"]["kwargs"].get("column", "N/A"),
            "success": e["success"],
            "element_count": e["result"].get("element_count", 0),
            "unexpected_count": e["result"].get("unexpected_count", 0),
            "success_percent": success_percent,
        }
        for e in expectation_results
    ]

    # Definir o schema (opcional, mas recomendado para tipos explícitos)
    schema = StructType(
        [
            StructField("run_name", StringType(), True),
            StructField("validation_time", StringType(), True),
            StructField("data_asset_name", StringType(), True),
            StructField("expectation_type", StringType(), True),
            StructField("column", StringType(), True),
            StructField("success", BooleanType(), True),
            StructField("element_count", IntegerType(), True),
            StructField("unexpected_count", IntegerType(), True),
            StructField("success_percent", DoubleType(), True),
        ]
    )

    # Criar o DataFrame PySpark
    result_df = spark.createDataFrame(rows, schema=schema)
    print(result_df.show(5, False))
    result_df.write.parquet(
        "s3://cjmm-mds-lake-curated/mds_data_quality_results/gx_amazonsales_glue_etl/",
        mode="append",
    )


def process_suite_ge(spark, input_path, output_path):
    df = read_data(spark, f"{input_path}/data-hands-on-df-soda-amazon-sales-obt/")

    df_ge = SparkDFDataset(df)

    context = create_context_ge(output_path)

    suite: ExpectationSuite = context.get_expectation_suite(
        expectation_suite_name=suite_name
    )

    add_profile_suite(context, df_ge)

    df_validator = create_validator(context, suite, df)
    df_validator = add_tests_suite(df_validator)

    results = df_validator.validate(expectation_suite=suite)
    context.build_data_docs(site_names=["s3_site"])

    process_results_gx(spark, results)

    print(results)
    if not results["success"]:
        print("A suite de testes foi executada com sucesso: " + str(results["success"]))
        print("Ação de validação caso seja necessário")
        Exception()


if __name__ == "__main__":
    input_path = "s3://cjmm-mds-lake-curated"
    output_path = "s3://datadocs-greatexpectations.cjmm"

    spark = create_spark_session()
    process_suite_ge(spark, input_path, output_path)
