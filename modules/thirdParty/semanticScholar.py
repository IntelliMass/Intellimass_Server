from math import floor
import requests
import json
import pandas as pd
import threading

from modules import utils
from modules.thirdParty import config


class SemanticScholarAPI:

    @staticmethod
    def __parallel_search(query: str, offset: int, queryResults: list):
        query = query.replace(' ', '+')
        url = f"http://api.semanticscholar.org/graph/v1/paper/search?query={query}&offset={offset}&limit={100}&fields=title,authors,isOpenAccess,fieldsOfStudy,year,abstract,venue"
        res = requests.get(url, headers=config.SemanticScholarheader)
        dictRes = json.loads(res.text)
        resData = dictRes['data']
        queryResults.extend(resData)

    @staticmethod
    def get_articles(query: str, num_of_articles=200, offset=0):

        queryResults = []
        roundedNumOfArticles = utils.roundup(num_of_articles)
        threads = []
        for num in range(roundedNumOfArticles):
            t = threading.Thread(target=SemanticScholarAPI.__parallel_search, args=(query, offset + num * 100, queryResults))
            threads.append(t)
            t.start()

        for thread in threads:
            thread.join()

        articles_df = pd.DataFrame(queryResults)
        return articles_df

    @staticmethod
    def get_one_article(article_id: str):
        return requests.get(f"https://api.semanticscholar.org/v1/paper/{article_id}", headers=config.SemanticScholarheader).text






