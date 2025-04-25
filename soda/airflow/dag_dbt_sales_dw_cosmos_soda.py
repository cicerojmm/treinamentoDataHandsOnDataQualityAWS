from airflow.decorators import dag
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python import PythonVirtualenvOperator
from airflow.operators.python import PythonOperator

from airflow.hooks.base import BaseHook

from cosmos import (
    DbtTaskGroup,
    ProjectConfig,
    ProfileConfig,
    RenderConfig,
    ExecutionConfig,
)
from cosmos.profiles import RedshiftUserPasswordProfileMapping
from cosmos.constants import TestBehavior

from pendulum import datetime
import boto3

from soda.scan import Scan

import pyarrow.parquet as pq
import pyarrow as pa
import io

import json
import pandas as pd

import uuid
import os

from utils import utils


conn = BaseHook.get_connection("aws_default")
aws_access_key = conn.login
aws_secret_key = conn.password
aws_region = "us-east-1"

CONNECTION_ID = "redshift_default"
DB_NAME = "amazonsales"
SCHEMA_NAME = "public"

# ROOT_PATH = "/opt/airflow/dags"
ROOT_PATH = "/usr/local/airflow/dags"
DBT_PROJECT_PATH = f"{ROOT_PATH}/dbt/sales_dw"


def gravar_resultados_soda_s3(data):
    datetime_tests = data.get("dataTimestamp")
    checks = data.get("checks", [])
    checks_data = []

    for check in checks:
        for metric in check.get("metrics", []):
            check_info = {
                "name": check.get("name"),
                "type": check.get("type"),
                "definition": check.get("definition"),
                "dataSource": check.get("dataSource"),
                "table": check.get("table"),
                "filter": check.get("filter"),
                "column": check.get("column"),
                "outcome": check.get("outcome"),
                "metric": metric,
            }
            checks_data.append(check_info)

    df = pd.DataFrame(checks_data)
    df["datetime"] = datetime_tests

    s3_bucket = "cjmm-datalake-curated"
    s3_path = (
        f"mds_data_quality_results/soda_amazonsales_airflow/{uuid.uuid4().hex}.parquet"
    )

    utils.salvar_dados_s3(df, s3_bucket, s3_path)


def run_soda_scan(project_root, scan_name, checks_subpath=None):
    config_file = f"{project_root}/configuration.yml"
    checks_path = f"{project_root}/checks"
    data_source = "amazonsales"

    if checks_subpath:
        checks_path += f"/{checks_subpath}"

    scan = Scan()
    scan.set_verbose()
    scan.add_configuration_yaml_file(config_file)
    scan.set_data_source_name(data_source)
    scan.add_sodacl_yaml_files(checks_path)
    scan.set_scan_definition_name(scan_name)

    scan.execute()
    scan.set_verbose(True)
    results = scan.get_scan_results()

    if scan.has_check_fails():
        utils.enviar_notificacao_sns(
            "dag_dbt_sales_dw_cosmos_soda",
            "airflow_soda_amazonsales",
            scan_name,
            scan.get_checks_fail_text(),
        )

    if results:
        gravar_resultados_soda_s3(results)

    print(results)


@dag(start_date=datetime(2025, 4, 1), schedule=None, catchup=False)
def dag_dbt_sales_dw_cosmos_soda():
    profile_config = ProfileConfig(
        profile_name="sales_dw",
        target_name="dev",
        profile_mapping=RedshiftUserPasswordProfileMapping(
            conn_id=CONNECTION_ID,
            profile_args={"schema": SCHEMA_NAME},
        ),
    )

    execution_config = ExecutionConfig(
        dbt_executable_path=f"{os.environ['AIRFLOW_HOME']}/dbt_venv/bin/dbt",
    )

    start_process = DummyOperator(task_id="start_process")

    transform_data = DbtTaskGroup(
        group_id="transform_data",
        project_config=ProjectConfig(DBT_PROJECT_PATH),
        profile_config=profile_config,
        execution_config=execution_config,
        render_config=RenderConfig(
            test_behavior=TestBehavior.NONE,
        ),
        default_args={"retries": 2},
    )

    checks_dw_soda_dims = PythonOperator(
        task_id="checks_dw_soda_dims",
        python_callable=run_soda_scan,
        op_kwargs={
            "project_root": f"{ROOT_PATH}/soda",
            "scan_name": "checks_dim_dw_amazon_sales",
            "checks_subpath": "dims",
        },
    )

    checks_dw_soda_facts = PythonOperator(
        task_id="checks_dw_soda_facts",
        python_callable=run_soda_scan,
        op_kwargs={
            "project_root": f"{ROOT_PATH}/soda",
            "scan_name": "checks_fact_dw_amazon_sales",
            "checks_subpath": "facts",
        },
    )

    start_process >> transform_data >> checks_dw_soda_dims >> checks_dw_soda_facts


dag_dbt_sales_dw_cosmos_soda()
