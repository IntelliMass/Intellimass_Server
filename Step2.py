import pandas as pd
import requests
import json
import threading
import time
import basicFlow.config as config


def extendPaperWithTopics(paperId: str, results: list):
    header = {"x-api-key": "qZWKkOKyzP5g9fgjyMmBt1MN2NTC6aT61UklAiyw"}
    url = f"https://api.semanticscholar.org/v1/paper/{paperId}"
    res = requests.get(url=url, headers=header)
    if res.status_code != 404:
        dictRes = json.loads(res.text)
        results.append(dictRes['topics'])
    else:
        results.append(None)


def extendArticles(dfOfArticles: pd.DataFrame, numOfResults):

    dfOfArticles.dropna(subset=['abstract'], inplace=True)
    results = []
    threads = []
    count = 0
    for _, article in dfOfArticles.iterrows():
        # print(article['paperId'])
        threads.append(threading.Thread(target=extendPaperWithTopics, args=(article['paperId'], results)))
        threads[count].start()
        count += 1
        if count % (config.MAX_THREAD_FOR_SEC - 1) == 0 and count != 0:
            time.sleep(1.6)

    for thread in threads:
        thread.join()

    dfOfArticles['topics'] = results
    dfOfArticles.drop(dfOfArticles[dfOfArticles['topics'].str.len() == 0].index, inplace=True)
    if len(dfOfArticles) > numOfResults:
        dfOfArticles = dfOfArticles.loc[:numOfResults]
    return dfOfArticles

