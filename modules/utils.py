from flask import request, Response
import json
import math
import pandas as pd
# from modules.algorithms import frequentWords, kmeans_lda
from modules import algorithms
from modules.db.objects import SessionObject
from modules.db import sessionsTable
from modules.thirdParty.semanticScholar import SemanticScholarAPI

#####################################################
# CONSTANTS CONSTANTS CONSTANTS CONSTANTS CONSTANTS #
#####################################################

PORT = 5000

COMMON_HEADER_RESPONSE = {
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': '*'
}

#####################################################

def roundup(x):
    """
    Round up to 100
    :param x: int
    :return:
    """
    return int(math.ceil(x / 100.0)) * 100


def get_post_data(*argv):
    """
    Extract post body by given *argv
    :param argv: Keys to extract from post body
    :return: Post Data -> tuple
    """
    data = []
    for key in argv:
        extractedKey = json.loads(request.data.decode('utf-8')).get(key)
        if extractedKey is None:
            return Response(response=f"Bad Request - {key}", status=400,
                            headers={'Access-Control-Allow-Origin': '*'})
        data.append(extractedKey)
    return tuple(data)


def get_query_params(*argv):
    """
    Extract query params from GET request
    :return:
    """
    data = []
    for key in argv:
        extractedKey = request.args.get(key)
        if extractedKey is None:
            return Response(response=f"Bad Request - {key}", status=400,
                            headers={'Access-Control-Allow-Origin': '*'})
        data.append(extractedKey)
    return tuple(data)

def clean_articles_df(articlesDF: pd.DataFrame):
    """
    CLean articles DF:
        * Faulted abstract
    :param articlesDF
    :return: articlesDF: pd.DataFrame
    """
    return articlesDF.dropna(subset=["abstract"], inplace=True)


def article_extender(articles_df: pd.DataFrame, query: str):
    """
    Extend articles DataFrame with frequent words & clusters (topics)
    :param articles_df:
    :param query:
    :return: articlesDF: pd.DataFrame
    """
    articlesDF = clean_articles_df(articles_df)
    articlesDF = algorithms.frequentWords.append(articlesDF, query)
    articlesDF = algorithms.kmeans_lda.LdaModeling(articlesDF).papers
    return articlesDF


def handle_articles_count(session_object: SessionObject, count: int):

    if count > len(session_object.articles):
        new_articles_df = SemanticScholarAPI.get_articles(session_object.query, offset=session_object.offset)
        session_object.articles.append(new_articles_df, ignore_index=True)
        session_object.articles = article_extender(session_object.articles, session_object.query)
        sessionsTable.update(session_object.id, session_object)
    else:
        return session_object.articles[:count]


def filter_articles_by_feature(articles_df: pd.DataFrame, filter_feature: str, filter_list: list):
    def any_wrapper(row, filterFeature, filterList):
        def list_to_lower_case(array: list): return [word.lower() for word in array]
        return any(freqWord in list_to_lower_case(row[filterFeature]) for freqWord in list_to_lower_case(filterList))
    return articles_df[articles_df.apply(any_wrapper, axis=1, args=(filter_feature, filter_list))]


def articles_to_json(articles_df: pd.DataFrame):
    return articles_df.to_dict('records')