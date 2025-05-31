import json
import boto3
import os

SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']

def lambda_handler(event, context):
    """
    Lambda function to handle Glue Data Quality error events from EventBridge
    and forward them to an SNS topic.
    """
    print(f"Received event: {json.dumps(event)}")

    
    # Extract relevant information from the event
    detail = event.get('detail', {})

    if detail:
        # Get the ruleset name and run ID
        ruleset_name = detail['rulesetNames'][0]
        pipeline = detail['context']["jobName"]
        
        # Prepare the message for SNS
        message_data = {
            "origem": "AWS Glue Data Quality",
            "pipeline": pipeline,
            "validacao": ruleset_name,
            "detalhes": f"""
                "state": {detail['state']},
                "timestamp": {event.get('time', '')}
            """
        }
        
        # Send to SNS
        sns_client = boto3.client('sns')
        response = sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="Glue Data Quality Alert",
            Message=json.dumps(message_data)
        )
        
        print(f"Message sent to SNS. MessageId: {response['MessageId']}")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Successfully processed Glue Data Quality event')
    }