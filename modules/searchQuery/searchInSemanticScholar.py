import requests
import pandas as pd
import json
import threading
import uuid
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
import string
from config.config_3rd_party import SemanticScholarheader


def appendMostFrequentFromAbstract(row, query):
    from collections import Counter
    abstract = row['abstract']

    MY_STOP = ['article', 'based', query.lower(), query.lower() + 's', query.lower() + "'s"]
    for sign in string.punctuation:
        abstract = abstract.replace(sign, '')

    splited = [word for word in abstract.split() if
               word.lower() not in ENGLISH_STOP_WORDS and word.lower() not in MY_STOP]
    Counter = Counter(splited)
    most_occur = Counter.most_common(5)
    row['frequentWords'] = [freqWord[0] for freqWord in most_occur]
    return row


def parallelSearch(query: str, offset:int, queryResults: list):
    query = query.replace(' ', '+')
    url = f"http://api.semanticscholar.org/graph/v1/paper/search?query={query}&offset={offset}&limit={100}&fields=title,authors,isOpenAccess,fieldsOfStudy,year,abstract,venue"
    res = requests.get(url, headers=SemanticScholarheader)
    dictRes = json.loads(res.text)
    resData = dictRes['data']
    queryResults.extend(resData)


def firstSearchQuerySemanticScholar(query: str):

    queryResults = []
    t1 = threading.Thread(target=parallelSearch, args=(query, 0, queryResults))
    t2 = threading.Thread(target=parallelSearch, args=(query, 100, queryResults))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    articlesDF = pd.DataFrame(queryResults)
    articlesDF.dropna(subset=["abstract"], inplace=True)
    print("___________________" + query)
    articlesDF = articlesDF.apply(appendMostFrequentFromAbstract, args=(query,), axis=1)
    articles = articlesDF.to_dict('records')
    resObject = {
        "query": query,
        "articles": articles,
        "id": str(uuid.uuid4()),
        "size": 200
    }
    return resObject

