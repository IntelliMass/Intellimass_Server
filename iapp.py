import json

import pandas as pd
from flask import request
from flask import Response
from modules import searchInSemanticScholar, extendArticlesList
from config import db_conn
import time
from modules.searchQuery import extendArticle
from multiprocessing import Process
from modules import getMetadata
from modules import getNetwork
from modules import filerArticlesByKeywords
from modules.algorithms import kmeans_lda
import os
from flask import Flask
from flask_cors import CORS
import requests as WebRequest
from config.config_3rd_party import SemanticScholarheader
from modules.utils import common_api_get_request
import sys
from waitress import serve

app = Flask(__name__)
CORS(app)


@app.route('/query', methods=['POST'])
def query():
    start = time.time()
    if request.method == 'POST':
        query = json.loads(request.data.decode('utf-8')).get('query')
        if query is None:
            return Response(response="Bad Request - query", status=400, headers={'Access-Control-Allow-Origin' : '*'})
        res = searchInSemanticScholar.firstSearchQuerySemanticScholar(query)
        print(f"time 1: {time.time() - start}")
        # p = Process(target=extendArticleBySemanticScholar.extendArticles, args=(res['articles'], res['id'], 0))
        p = Process(target=extendArticle.extendArticles, args=(res['articles'], res['id'], 0))
        p.daemon = True
        p.start()
        db_conn.sessionsDB.insert_one(res)
        print(f"time 2: {time.time() - start}")

        headers = {
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': '*'
        }
        return Response(response=json.dumps({'queryId': res['id']}), status=200, headers=headers)


@app.route('/articles')
def get_articles():
    articles, count, obj = common_api_get_request()

    # Extend if needed
    if count > len(articles):
        articles, size = extendArticlesList(obj)
        p = Process(target=extendArticle.extendArticles, args=(articles, obj['id'], obj['size']))
        p.daemon = True
        p.start()
        setParams = {"$set": {'articles': articles, 'size': size}}
        updateFilter = {'id': obj['id']}
        db_conn.sessionsDB.update_one(updateFilter, setParams)

    articles = articles[:count]
    # Filter
    filterFeature = request.args.get('filterFeature')
    filterList = request.args.get('filterList')
    if filterFeature is not None and filterFeature != "" and filterList is not None and filterList != "":
        filterList = filterList.split(',')
        articles = filerArticlesByKeywords(articles, filterList, filterFeature)

    return {"articles": articles[:count]}


@app.route('/metadata')
def get_metadata():
    articles, count, obj = common_api_get_request()
    articles = articles[:count]

    # Filter
    filterFeature = request.args.get('filterFeature')
    filterList = request.args.get('filterList')
    if filterFeature is not None and filterFeature != "" and filterList is not None and filterList != "":
        filterList = filterList.split(',')
        articles = filerArticlesByKeywords(articles, filterList, filterFeature)

    mostCommonFrequentWords = getMetadata(articles)
    return {"mostCommonFrequentWords": mostCommonFrequentWords}


@app.route('/network')
def get_network():
    articles, count, obj = common_api_get_request()
    articles = articles[:count]
    feature = request.args.get('feature')
    if feature is None:
        feature = 'authors'

    # Filter
    filterFeature = request.args.get('filterFeature')
    filterList = request.args.get('filterList')
    if filterFeature is not None and filterFeature != "" and filterList is not None and filterList != "":
        filterList = filterList.split(',')
        articles = filerArticlesByKeywords(articles, filterList, filterFeature)

    links = getNetwork(articles, feature)

    return {
            "nodes": articles,
            "links": links
        }


@app.route('/getOne', methods=['GET'])
def getOne():
    paperId = request.args.get('id')
    if paperId is None:
        return Response(response="Bad Request - id",
                        headers={'Access-Control-Allow-Origin': '*'},
                        status=400)
    if paperId == "":
        return Response(response="Bad Request - id empty",
                        headers={'Access-Control-Allow-Origin': '*'},
                        status=400)
    return WebRequest.get(f"https://api.semanticscholar.org/v1/paper/{paperId}", headers=SemanticScholarheader).text


@app.route('/categories', methods=['GET'])
def get_categories():
    articles, count, obj = common_api_get_request()
    articles = articles[:count]
    df_articles = pd.DataFrame(articles)
    list_categories = list(df_articles['categories'].unique())
    return {"articleCategories": list_categories}


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1].lower() == 'prod':
        serve(app, host="0.0.0.0", port=5000)
    else:
        # context = ('cert.pem', 'server.key')
        # app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)), ssl_context=context)
        app.run(host='0.0.0.0', debug=True, port=int(os.environ.get("PORT", 5000)))
