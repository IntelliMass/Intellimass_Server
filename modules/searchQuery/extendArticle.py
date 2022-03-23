import pandas as pd
import requests
import json
import threading
import time
from config.db_conn import sessionsDB
from config.config_3rd_party import SemanticScholarheader
from ..algorithms.kmeans_lda import LdaModeling
MAX_THREAD_FOR_SEC = 100


def extendPaperWithTopics(paperId: str, topics: list, references: list):
    url = f"https://api.semanticscholar.org/v1/paper/{paperId}"
    res = requests.get(url=url, headers=SemanticScholarheader)
    if res.status_code != 404:
        dictRes = json.loads(res.text)
        try:
            topics.append(dictRes['topics'])
        except KeyError:
            topics.append(None)
        try:
            references.append(dictRes['references'])
        except KeyError:
            references.append(None)
    else:
        topics.append(None)
        references.append(None)


def extendArticles(listOfArticles: list, id: str, offset: int):
    start = time.time()
    dfOfArticles = pd.DataFrame(listOfArticles)
    dfOfArticles.dropna(subset=['abstract'], inplace=True)
    topics = []
    references = []
    threads = []
    count = 0
    for _, article in dfOfArticles[offset:].iterrows():
        threads.append(threading.Thread(target=extendPaperWithTopics, args=(article['paperId'], topics, references)))
        threads[count].start()
        count += 1
        if count % (MAX_THREAD_FOR_SEC - 1) == 0 and count != 0:
            time.sleep(1.6)

    for thread in threads:
        thread.join()

    if 'topics' not in dfOfArticles.columns:
        dfOfArticles['topics'] = topics
    else:
        dfOfArticles.loc[offset:]['topics'] = topics
    if 'references' not in dfOfArticles.columns:
        dfOfArticles['references'] = references
    else:
        dfOfArticles.loc[offset:]['references'] = references

    dfOfArticles.drop(dfOfArticles[dfOfArticles['topics'].str.len() == 0].index, inplace=True)
    dfOfArticles.drop(dfOfArticles[dfOfArticles['references'].str.len() == 0].index, inplace=True)

    # kmeans append clusters
    processed_data = LdaModeling(dfOfArticles)
    dfOfArticles = processed_data.papers

    listOfArticles = dfOfArticles.to_dict('records')
    sessionsDB.update_one(filter={"id": id}, update={"$set": {"articles": listOfArticles}})
    print(f"time to extend with scholar: {time.time() - start}")



