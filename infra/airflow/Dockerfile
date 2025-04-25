FROM apache/airflow:2.10.5

WORKDIR /opt/airflow

# Troca para root temporariamente para instalar dependências do sistema
USER root
RUN apt-get update && apt-get install -y libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Criando ambiente virtual para o DBT
ENV DBT_VENV_PATH="/opt/airflow/dbt_venv"

RUN python3 -m venv "${DBT_VENV_PATH}" \
    && ${DBT_VENV_PATH}/bin/pip install --no-cache-dir dbt-redshift

# Volta para o usuário padrão do Airflow
USER airflow

# Copia e instala dependências do Airflow
COPY ./requirements.txt /opt/airflow/requirements.txt
RUN pip install --no-cache-dir -r /opt/airflow/requirements.txt
