from pendulum import datetime
from airflow.decorators import dag
from airflow import DAG
from great_expectations_provider.operators.great_expectations import (
    GreatExpectationsOperator,
)
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup

import pandas as pd
import uuid

from utils import utils

POSTGRES_CONN_ID = "postgres_default"
MY_POSTGRES_SCHEMA = "public"
# MY_GX_DATA_CONTEXT = "/opt/airflow/dags/great_expectations"
MY_GX_DATA_CONTEXT = "/tmp/great_expectations"

ASSETS = [
    "dim_product",
    "dim_rating",
    "dim_user",
    "fact_product_rating",
    "fact_sales_category",
]


def enviar_notificacao(gx_result, task_name, details):
    if not gx_result["success"]:
        utils.enviar_notificacao_sns(
            "dag_great_expectations_dw_tests",
            task_name,
            "Many Expectations",
            details,
        )


def process_gx_result(asset_name: str, **kwargs):
    task_name = f"gx_validation_group.gx_validate_redshift_{asset_name}"
    ti = kwargs["ti"]
    gx_result = ti.xcom_pull(task_ids=task_name)

    enviar_notificacao(gx_result, task_name, ti.log_url)

    run_name = gx_result["run_id"]["run_name"]
    result_data = list(gx_result["run_results"].values())[0]["validation_result"]

    validation_time = result_data["meta"]["validation_time"]
    batch_info = result_data["meta"]["active_batch_definition"]
    expectation_results = result_data["results"]
    success_percent = result_data["statistics"]["success_percent"]

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

    df = pd.DataFrame(rows)
    utils.salvar_dados_s3(
        df,
        "cjmm-datalake-mds-curated",
        f"mds_data_quality_results/gx_amazonsales_airflow/{uuid.uuid4().hex}.parquet",
    )

    # Retorna o dataframe em forma de dict para uso posterior
    return df.to_dict(orient="records")


def aggregate_results(**kwargs):
    ti = kwargs["ti"]
    all_results = []

    for asset in ASSETS:
        result = ti.xcom_pull(task_ids=f"gx_validation_group.process_results_tests_{asset}")
        if result:
            all_results.extend(result)

    df = pd.DataFrame(all_results)
    utils.salvar_dados_s3(
        df,
        "cjmm-datalake-mds-curated",
        f"mds_data_quality_results/gx_amazonsales_airflow/final_{uuid.uuid4().hex}.parquet",
    )


import shutil, os


def prepare_gx_context_local():
    source_dir = "/usr/local/airflow/dags/great_expectations"
    target_dir = "/tmp/great_expectations"

    # Remove se já existir e recria
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)
    shutil.copytree(source_dir, target_dir)


def create_gx_and_process_tasks(dag: DAG, first_task):

    # Cria o Task Group para agrupar todas as tasks de validação
    with TaskGroup(
        "gx_validation_group", tooltip="Validações do Great Expectations"
    ) as gx_group:
        previous_task = None

        for idx, asset in enumerate(ASSETS):
            gx_task = GreatExpectationsOperator(
                task_id=f"gx_validate_redshift_{asset}",
                conn_id=POSTGRES_CONN_ID,
                data_context_root_dir=MY_GX_DATA_CONTEXT,
                schema=MY_POSTGRES_SCHEMA,
                data_asset_name=asset,
                expectation_suite_name=f"amazonsales_{asset}_suite",
                return_json_dict=True,
                fail_task_on_validation_failure=False,
                dag=dag,
            )

            process_task = PythonOperator(
                task_id=f"process_results_tests_{asset}",
                python_callable=process_gx_result,
                op_kwargs={"asset_name": asset},
                provide_context=True,
                dag=dag,
            )

            # Só conecta a primeira task com a primeira gx_task
            if idx == 0:
                first_task >> gx_task

            # Conecta a task anterior à atual (sequencialmente)
            if previous_task:
                previous_task >> gx_task

            gx_task >> process_task
            previous_task = process_task

    return previous_task  # última task do encadeamento


with DAG(
    "dag_great_expectations_dw_tests",
    start_date=datetime(2025, 4, 1),
    schedule=None,
    catchup=False,
    description="Validações de dados com GX sem falhar a DAG",
) as dag:

    gx_prepare_context_task = PythonOperator(
        task_id="prepare_gx_context_local",
        python_callable=prepare_gx_context_local,
        dag=dag,
    )

    gx_last_process_task = create_gx_and_process_tasks(dag, gx_prepare_context_task)

    gx_aggregate_task = PythonOperator(
        task_id="gx_aggregate_results",
        python_callable=aggregate_results,
        provide_context=True,
    )

    gx_last_process_task >> gx_aggregate_task
