from math import floor
import requests
import json
import pandas as pd
import threading
from modules import utils
from modules.thirdParty import config
import time

class SemanticScholarAPI:
    MAX_THREAD_FOR_SEC = 100

    @staticmethod
    def __parallel_search(query: str, offset: int, queryResults: list):
        query = query.replace(' ', '+')
        url = f"http://api.semanticscholar.org/graph/v1/paper/search?query={query}&offset={offset}&limit=100&fields=title,authors,isOpenAccess,fieldsOfStudy,year,abstract,venue"
        res = requests.get(url, headers=config.SemanticScholarheader)
        dictRes = json.loads(res.text)
        resData = dictRes['data']
        queryResults.extend(resData)

    @staticmethod
    def extendPaperWithTopics(paperId: str, topics: list, references: list):
        url = f"https://api.semanticscholar.org/v1/paper/{paperId}"
        res = requests.get(url=url, headers=config.SemanticScholarheader)
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

    @staticmethod
    def extendArticles(listOfArticles: list):
        dfOfArticles = pd.DataFrame(listOfArticles)
        dfOfArticles.dropna(subset=['abstract'], inplace=True)
        topics = []
        references = []
        threads = []
        count = 0
        for _, article in dfOfArticles.iterrows():
            threads.append(
                threading.Thread(target=SemanticScholarAPI.extendPaperWithTopics, args=(article['paperId'], topics, references)))
            threads[count].start()
            count += 1
            if count % (SemanticScholarAPI.MAX_THREAD_FOR_SEC - 1) == 0 and count != 0:
                time.sleep(1.6)

        for thread in threads:
            thread.join()

        print(f"lenOfArticles: {len(dfOfArticles)} lenOfTopics: {len(topics)} offset")
        dfOfArticles['topics'] = topics
        dfOfArticles['references'] = references
        # if 'topics' not in dfOfArticles.columns:
        #     dfOfArticles['topics'] = topics
        # else:
        #     dfOfArticles.loc[offset:]['topics'] = topics
        # if 'references' not in dfOfArticles.columns:
        #     dfOfArticles['references'] = references
        # else:
        #     dfOfArticles.loc[offset:]['references'] = references

        dfOfArticles.drop(dfOfArticles[dfOfArticles['topics'].str.len() == 0].index, inplace=True)
        dfOfArticles.drop(dfOfArticles[dfOfArticles['references'].str.len() == 0].index, inplace=True)
        return dfOfArticles

    @staticmethod
    def get_articles(query: list, operator: str, num_of_articles=200, offset=0):
        queryResults = []
        threads = []
        if operator.upper() == 'AND':
            roundedNumOfArticles = utils.roundup(num_of_articles)
            print(query)
            query = "".join([q + '+' for q in query]).replace(' ',  '+')
            for num in range(0, roundedNumOfArticles, 100):
                t = threading.Thread(target=SemanticScholarAPI.__parallel_search, args=(query, offset + num, queryResults))
                threads.append(t)
                t.start()
            for thread in threads:
                thread.join()

        if operator.upper() == 'OR':
            roundedNumOfArticles = utils.roundup(floor(num_of_articles/len(query)))
            for q in query:
                for num in range(0, roundedNumOfArticles, 100):
                    t = threading.Thread(target=SemanticScholarAPI.__parallel_search,
                                         args=(q, utils.roundup(offset + num), queryResults))
                    threads.append(t)
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

        articles_df = SemanticScholarAPI.extendArticles(queryResults)
        # articles_df = pd.DataFrame(queryResults).sample(frac=1).reset_index(drop=True)
        return articles_df

    @staticmethod
    def get_one_article(article_id: str):
        return requests.get(f"https://api.semanticscholar.org/v1/paper/{article_id}", headers=config.SemanticScholarheader).text






