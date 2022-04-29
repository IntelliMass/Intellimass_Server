from flask import request, Response
import json
import math
import pandas as pd
# from modules.algorithms import frequentWords, kmeans_lda
from modules import algorithms

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
    Extract post data by given *argv
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


def get_query_params():
    """
    Extract query params from GET request
    :return:
    """
    queryId = request.args.get('id')
    if queryId is None:
        return Response(response="Bad Request - id",
                        headers={'Access-Control-Allow-Origin': '*'},
                        status=400)
    if queryId == "":
        return Response(response="Bad Request - id empty",
                        headers={'Access-Control-Allow-Origin': '*'},
                        status=400)

    count = request.args.get('count')
    if count is None:
        count = 100
    try:
        count = int(count)
    except TypeError:
        raise Response(response="Bad Request - count", headers={'Access-Control-Allow-Origin': '*'}, status=200)
    return queryId, count


def clean_articles_df(articlesDF: pd.DataFrame):
    """
    CLean articles DF:
        * Faulted abstract
    :param articlesDF
    :return: articlesDF: pd.DataFrame
    """
    return articlesDF.dropna(subset=["abstract"], inplace=True)


def article_extender(articlesDF: pd.DataFrame, query: str):
    """
    Extend articles DataFrame with frequent words & clusters (topics)
    :param articlesDF
    :return: articlesDF: pd.DataFrame
    """
    articlesDF = clean_articles_df(articlesDF)
    articlesDF = algorithms.frequentWords.append(articlesDF, query)
    articlesDF = algorithms.kmeans_lda.LdaModeling(articlesDF).papers
    return articlesDF

