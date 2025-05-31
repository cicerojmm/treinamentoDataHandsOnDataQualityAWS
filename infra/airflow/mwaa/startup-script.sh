#!/bin/sh

export DBT_VENV_PATH="${AIRFLOW_HOME}/dbt_venv"
export PIP_USER=false

python3 -m venv "${DBT_VENV_PATH}"

${DBT_VENV_PATH}/bin/pip install dbt-redshift

export PIP_USER=true