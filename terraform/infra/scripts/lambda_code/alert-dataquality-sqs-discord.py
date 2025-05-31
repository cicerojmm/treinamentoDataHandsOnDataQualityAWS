import json
import urllib.request
import os

DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

def send_to_discord(message):
    """Envia uma mensagem para o canal do Discord via Webhook."""
    data = {"content": message}

    req = urllib.request.Request(DISCORD_WEBHOOK_URL, data=json.dumps(data).encode("utf-8"))
    req.add_header('Content-Type', 'application/json')
    req.add_header('User-Agent', 'Mozilla/5.0')

    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 204:
                print("✅ Mensagem enviada com sucesso ao Discord.")
            else:
                print(f"⚠️ Falha ao enviar mensagem: {response.status}")
    except Exception as e:
        print(f"❌ Erro ao enviar mensagem ao Discord: {e}")

def lambda_handler(event, context):
    """Função Lambda para processar mensagens do SNS e enviá-las ao Discord."""
    for record in event['Records']:
        # O SNS envia mensagens como string, então precisamos converter para JSON
        sns_message = json.loads(record['Sns']['Message'])

        # Extraindo dados da mensagem
        origem = sns_message.get('origem', 'Desconhecido')
        pipeline = sns_message.get('pipeline', 'Desconhecido')
        validacao = sns_message.get('validacao', 'Desconhecido')
        detalhes = sns_message.get('detalhes', 'Desconhecido')

        # Montando a mensagem para o Discord
        discord_message = f"📢 **Data Quality Alert**:\n**Origem**: {origem}\n**Pipeline**: {pipeline}\n**Validação**: {validacao}\n**Detalhes**: {detalhes}"

        # Enviar a mensagem ao Discord
        send_to_discord(discord_message)

        print(f"📨 Processado e registrado no Discord: {record['Sns']['MessageId']}")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Mensagens do SNS processadas com sucesso')
    }
