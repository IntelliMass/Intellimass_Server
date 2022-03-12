import json
import base64
from main import handleQuery


def lambda_handler(event, context):
    print(type(event))
    if 'isBase64Encoded' in event.keys() and event['isBase64Encoded'] is True:
        body = base64.b64decode(event['body']).decode('utf-8')

    elif 'body' in event.keys() and type(event['body']) is str:
        body = event['body']
        body = body.replace("'", "\"")
        body = json.loads(body)
    else:
        body = event

    try:
        query = body['query']
        numOfResults = body['num_of_results']
    except KeyError:
        query = "IOT"
        numOfResults = 100

    resBody = handleQuery(query, numOfResults)

    return {
        'statusCode': 200,
        'body': json.dumps(resBody)
    }
