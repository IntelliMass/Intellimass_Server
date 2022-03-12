import requests
import json
import threading
import pandas as pd
import boto3
import time
import os

MAX_THREAD_FOR_SEC = int(os.environ['MAX_THREAD_FOR_SEC'])

def extendPaperWithTopics(paperId: str, results: list):
    header = {"x-api-key": "qZWKkOKyzP5g9fgjyMmBt1MN2NTC6aT61UklAiyw"}
    url = f"https://api.semanticscholar.org/v1/paper/{paperId}"
    res = requests.get(url=url, headers=header)
    if res.status_code != 404:
        dictRes = json.loads(res.text)
        results.append(dictRes['topics'])
    else:
        results.append(None)


def extendArticles(articles: list):
    dfOfArticles = pd.DataFrame(articles)
    results = []
    threads = []
    count = 0
    for _, article in dfOfArticles.iterrows():
        threads.append(threading.Thread(target=extendPaperWithTopics, args=(article['paperId'], results)))
        threads[-1].start()
        count += 1
        if count % (MAX_THREAD_FOR_SEC - 1) == 0 and count != 0:
            time.sleep(1.6)

    for thread in threads:
        thread.join()

    dfOfArticles['topics'] = results
    dfOfArticles.drop(dfOfArticles[dfOfArticles['topics'].str.len() == 0].index, inplace=True)
    return dfOfArticles.to_dict("records")

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    key = event['Records'][0]['s3']['object']['key']

    object = s3.get_object(Bucket='intellimass-sessions', Key=key)
    sessionData = json.loads(object['Body'].read())
    ID = sessionData['Id']

    articles = sessionData['articles']
    sessionData['articles'] = extendArticles(articles)

    s3.put_object(
        Body=json.dumps(sessionData).encode('UTF-8'),
        Bucket="intellimass-sessions",
        Key="STEP2/" + ID
    )

    s3.delete_object(
        Bucket="intellimass-sessions",
        Key="STEP1/" + ID
    )


