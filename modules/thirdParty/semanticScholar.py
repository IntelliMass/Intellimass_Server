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
        """
        Thread Function
        :param query: User's query
        :param offset: offset of articles searched for Semantic Scholar API
        :param queryResults: Searchts in DataFrame
        :return:
        """
        query = query.replace(' ', '+')
        url = f"http://api.semanticscholar.org/graph/v1/paper/search?query={query}&offset={offset}&limit=100&fields=title,authors,isOpenAccess,fieldsOfStudy,year,abstract,venue"
        res = requests.get(url, headers=config.SemanticScholarheader)
        dictRes = json.loads(res.text)
        resData = dictRes['data']
        queryResults.extend(resData)

    @staticmethod
    def extendPaperWithTopics(paperId: str, topics: list, references: list):
        """
        For each paper get the topics provided by the API and push to the articles list.
        Topics is not provided in the basic search only article by article.
        :param paperId: UID of paper in Semantic Scholar :type str
        :param topics: list of topics :type list
        :param references: list of references :type list
        """
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

        dfOfArticles['topics'] = topics
        dfOfArticles['references'] = references

        dfOfArticles.drop(dfOfArticles[dfOfArticles['topics'].str.len() == 0].index, inplace=True)
        dfOfArticles.drop(dfOfArticles[dfOfArticles['references'].str.len() == 0].index, inplace=True)
        return dfOfArticles

    @staticmethod
    def get_articles(query: list, operator: str, num_of_articles=200, offset=0):
        """

        :param query: User's query :type list
        :param operator: Operator provided by user :type str
        :param num_of_articles: :type int
        :param offset: :type int
        :return: Dataframe of articles :type pd.DataFrame
        """
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
        return articles_df

    @staticmethod
    def get_one_article(article_id: str):
        """
        :param article_id: UID of paper in Semantic Scholar :type str
        :return: object of the artciels metadata :type dict
        """
        return requests.get(f"https://api.semanticscholar.org/v1/paper/{article_id}", headers=config.SemanticScholarheader).text






