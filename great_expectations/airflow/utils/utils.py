from airflow.hooks.base import BaseHook

import boto3
import json
import io


def get_aws_credentials():
    conn = BaseHook.get_connection("aws_default")
    aws_access_key = conn.login
    aws_secret_key = conn.password
    aws_region = "us-east-2"

    return aws_access_key, aws_secret_key, aws_region


def enviar_notificacao_sns(origem, pipeline, validacao, detalhes):
    topic_arn = "arn:aws:sns:us-east-2:<account>:data-handson-dq-alerts-dev"
    message_data = {
        "origem": origem,
        "pipeline": pipeline,
        "validacao": validacao,
        "detalhes": detalhes,
    }

    aws_access_key, aws_secret_key, aws_region = get_aws_credentials()
    sns_client = boto3.client(
        "sns",
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=aws_region,
    )

    response = sns_client.publish(
        TopicArn=topic_arn,
        Subject="alert-dq-pipelines",
        Message=json.dumps(message_data),
    )

    print(f"Mensagem enviada! MessageId: {response['MessageId']}")
    return response


def salvar_dados_s3(df, s3_bucket, s3_path):
    buffer = io.BytesIO()
    aws_access_key, aws_secret_key, aws_region = get_aws_credentials()
    df.to_parquet(buffer, engine="pyarrow")

    s3 = boto3.client(
        "s3",
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=aws_region,
    )
    
    s3.put_object(Bucket=s3_bucket, Key=s3_path, Body=buffer.getvalue())