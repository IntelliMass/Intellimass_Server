#######
# endpoint: /query [POST]
#######

import uuid
import boto3
import time
import json


def postQuery(query: dict):
    """

    :param query:   {
                        "query": str
                    }
    """

    query = query.update({"Id": str(uuid.uuid4()), "timestamp": int(time.time())})
    dynamodb = boto3.client('dynamodb')
    dynamodb.put_item(TableName='QueriesCache', Item=query)


def lambda_handler(event, context):

    if event is dict:
        body = event

    else:
        body = event['body']

    query = body['query']
    postQuery(query)

    return {
        'statusCode': 200,
        'body': json.dumps('Success')
    }
