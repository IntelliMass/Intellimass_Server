from flask import request, Response
import json
import math
import pandas as pd
# from modules.algorithms import frequentWords, kmeans_lda
from modules import algorithms


def roundup(x):
    """
    Round up to 100
    :param x: int
    :return:
    """
    return int(math.ceil(x / 100.0)) * 100


def getPostData(*argv):
    """
    :param argv: Keys to extract from post body
    :return: Post Data
    """
    data = []
    for key in argv:
        extractedKey = json.loads(request.data.decode('utf-8')).get(key)
        if extractedKey is None:
            return Response(response=f"Bad Request - {key}", status=400,
                            headers={'Access-Control-Allow-Origin': '*'})
        data.append(extractedKey)
    return tuple(data)

def getQueryParams():
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

        return Response(response="Bad Request - count", headers={'Access-Control-Allow-Origin': '*'}, status=200)


def cleanArticlesDF(articlesDF: pd.DataFrame):
    return articlesDF.dropna(subset=["abstract"], inplace=True)


def articleExtender(articlesDF: pd.DataFrame, query: str):
    """

    :param articlesDF:
    :return:
    """
    articlesDF = cleanArticlesDF(articlesDF)
    articlesDF = algorithms.frequentWords.append(articlesDF, query)
    articlesDF = algorithms.kmeans_lda.LdaModeling(articlesDF).papers
    return articlesDF
