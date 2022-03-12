import requests
import json
import boto3
import pandas as pd
import threading
import math


def searchThread(query: str, offset: int, results: list):

    header = {"x-api-key": "qZWKkOKyzP5g9fgjyMmBt1MN2NTC6aT61UklAiyw"}
    url = f"http://api.semanticscholar.org/graph/v1/paper/search?query={query}&offset={offset}&limit=100&fields=title,authors,isOpenAccess,fieldsOfStudy,year,abstract"
    res = requests.get(url, headers=header)

    dictRes = json.loads(res.text)
    resData = dictRes['data']
    results.extend(resData)


def searchQuerySemanticScholar(query: str, numOfResults: int, ID:str):
    query = query.replace(' ', '+')
    queryResults = []
    counter = 0

    results = []
    threads = []
    for i in range(math.trunc(numOfResults/100)):
        threads.append(threading.Thread(target=searchThread, args=(query, i*100, results)))
        threads[i].start()

    for i in range(math.trunc(numOfResults/100)):
        threads[i].join()

    df = pd.DataFrame(results)
    df.dropna(subset=['abstract'], inplace=True)
    resData = df.to_dict("records")

    s3 = boto3.client('s3')
    item = s3.get_object(Bucket="intellimass-sessions", Key=f"POST/{ID}")["Body"].read().decode('utf-8')
    data = json.loads(item)
    data.update({'articles': resData})

    s3.put_object(
        Body=json.dumps(data).encode('UTF-8'),
        Bucket="intellimass-sessions",
        Key="STEP1/" + ID
    )

    s3.delete_object(
        Bucket="intellimass-sessions",
        Key="POST/" + ID
    )

def lambda_handler(event, context):

    searchQuerySemanticScholar(event['query'], event['numOfResults'], event['id'])