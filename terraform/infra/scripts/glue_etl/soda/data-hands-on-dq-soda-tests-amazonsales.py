import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from awsglue.utils import getResolvedOptions
from soda.scan import Scan
from pyspark.sql import Row
from pyspark.sql.types import StructType, StructField, StringType
import json
import pandas as pd

def create_spark_session(app_name="spark-app"):
    return (SparkSession.builder
        .appName("CuratedLayer")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .getOrCreate())


def read_data(spark, file_path):
    df = spark.read.format("delta").load(file_path)
    df.createOrReplaceTempView("amazonsales")
    return df

def configure_soda_scan(spark):
    scan = Scan()
    scan.add_configuration_yaml_str(
    """
        data_source amazonsales:
          type: spark_df
    """
    )
    scan.set_data_source_name("amazonsales")
    scan.add_spark_session(spark, data_source_name="amazonsales")
    return scan

def add_soda_checks(scan):
    checks = """
    checks for amazonsales:
      - schema:
          fail:
             when required column missing: [product_id, product_name, category, discounted_price, actual_price, discount_percentage, rating, rating_count, about_product, user_id, user_name, review_id, review_title, review_content, img_link, product_link]

      - missing_count(product_id) = 0:
          fail: when > 0

      - missing_count(product_name) = 0:
          fail: when > 0

      - duplicate_count(product_id) = 0:
          warn: when > 0

      - missing_count(discounted_price) < 10%:
          warn: when > 10%

      - missing_count(actual_price) < 10%:
          warn: when > 10%

      - missing_count(discount_percentage) < 10%:
          warn: when > 10%

      - missing_count(rating) < 20%:
          warn: when > 20%

      - missing_count(rating_count) < 20%:
          warn: when > 20%
      
      - invalid_percent(discount_percentage) < 100:
          fail: when >= 100

      - min(discounted_price) > 0:
          fail: when <= 0

      - min(actual_price) > 0:
          fail: when <= 0

      - invalid_percent(rating) between 0 and 5:
          fail: when < 0 or > 5

      - duplicate_count(review_id) = 0:
          fail: when > 0
          
      # Validação de tipos de dados
      - invalid_percent(discounted_price, decimal) = 0:
          fail: when > 5%
    
      - invalid_percent(actual_price, decimal) = 0:
          fail: when > 5%
    
      - invalid_percent(discount_percentage, decimal) = 0:
          fail: when > 5%
    
      - invalid_percent(rating, decimal) = 0:
          fail: when > 5%
    
      - invalid_percent(rating_count, integer) = 0:
          fail: when > 5%
    
      - invalid_percent(product_id, integer) = 0:
          fail: when > 5%
    
      - invalid_percent(user_id, integer) = 0:
          fail: when > 5%
    
      - invalid_percent(review_id, integer) = 0:
          fail: when > 5%
    """
    scan.add_sodacl_yaml_str(checks)

def execute_soda_scan(scan):
    scan.execute()
    scan.set_verbose(True)
    #scan.set_scan_definition_name("")
    return scan.get_scan_results()

def process_scan_results(data):
    schema = StructType([
        StructField("name", StringType(), True),
        StructField("type", StringType(), True),
        StructField("definition", StringType(), True),
        StructField("dataSource", StringType(), True),
        StructField("table", StringType(), True),
        StructField("filter", StringType(), True),
        StructField("column", StringType(), True),
        StructField("outcome", StringType(), True),
        StructField("metric", StringType(), True),
        StructField("datetime", StringType(), True)
    ])
    
    checks_data = [
        Row(
            name=str(check.get("name", "")),
            type=str(check.get("type", "")),
            definition=str(check.get("definition", "")),
            dataSource=str(check.get("dataSource", "")),
            table=str(check.get("table", "")),
            filter=str(check.get("filter", "")),
            column=str(check.get("column", "")),
            outcome=str(check.get("outcome", "")),
            metric=str(metric),
            datetime=str(data.get("dataTimestamp", ""))
        )
        for check in data.get("checks", [])
        for metric in check.get("metrics", [])
    ]
    
    return checks_data, schema

def write_results_to_s3(spark, checks_data, schema, output_path):
    df_spark = spark.createDataFrame(checks_data, schema=schema)
    df_spark.write.mode("append").parquet(output_path)

def main():
    spark = create_spark_session()
    df = read_data(spark, "s3://cjmm-mds-lake-curated/data-hands-on-df-soda-amazon-sales-obt")
    
    scan = configure_soda_scan(spark)
    add_soda_checks(scan)
    
    results = execute_soda_scan(scan)
    print("## results")
    print(results)
    
    checks_data, schema = process_scan_results(results)
    
    write_results_to_s3(spark, checks_data, schema, "s3://cjmm-mds-lake-curated/mds_data_quality_results/soda_amazonsales_spark")

if __name__ == "__main__":
    main()
