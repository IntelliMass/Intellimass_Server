from math import floor
import requests
import json
import pandas as pd
import threading

from modules import utils
from modules.thirdParty import config


class SemanticScholarAPI:

    @staticmethod
    def __parallelSearch(query: str, offset: int, queryResults: list):
        query = query.replace(' ', '+')
        url = f"http://api.semanticscholar.org/graph/v1/paper/search?query={query}&offset={offset}&limit={100}&fields=title,authors,isOpenAccess,fieldsOfStudy,year,abstract,venue"
        res = requests.get(url, headers=config.SemanticScholarheader)
        dictRes = json.loads(res.text)
        resData = dictRes['data']
        queryResults.extend(resData)

    @staticmethod
    def getArticles(query: str, numOfArticles = 200):

        queryResults = []
        roundedNumOfArticles = utils.roundup(numOfArticles)
        threads = []
        for num in range(roundedNumOfArticles):
            t = threading.Thread(target=SemanticScholarAPI.__parallelSearch, args=(query, 0, queryResults))
            threads.append(t)
            t.start()

        for thread in threads:
            thread.join()

        articlesDF = pd.DataFrame(queryResults)



