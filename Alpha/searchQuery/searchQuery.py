import json
import boto3

def lambda_handler(event, context):
    if event['Records'][0]['eventName'] != 'INSERT':
        return

    ID = event['Records'][0]['dynamodb']['NewImage']['Id']['S']
    query = event['Records'][0]['dynamodb']['NewImage']['query']['S']

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }