import sys
import os
from flask import Flask, Response
from flask_cors import CORS
import time
import json

###################################################
# MODULES MODULES MODULES MODULES MODULES MODULES #
from modules import utils
from modules.thirdParty import SemanticScholarAPI, config
from modules.db import sessionsTable, privateCollectionsTable, objects
from modules.network import Network
# MODULES MODULES MODULES MODULES MODULES MODULES #
###################################################

app = Flask(__name__)
CORS(app)


@app.route('/query', methods=['POST'])
def query():
    """
    Steps:
        1. Get articles from 3rd party
            rawArticles class :     {
                                        title: str,authors: list[str],
                                        isOpenAccess: bool,
                                        fieldsOfStudy: list[str],
                                        year: int,
                                        abstract: str,
                                        venue: str
                                    }
        2. Append to each article frequent words & topics.
        3. Insert to Database
    :response: 200/400
    """

    start = time.time()
    try:
        (query,) = utils.get_post_data('query')
    except Response as res:
        return res
    raw_articles = SemanticScholarAPI.get_articles(query)
    extended_articles = utils.article_extender(raw_articles, query)
    object = objects.SessionObject(query, extended_articles, config.Defaults.numOfArticles_firstSearch)
    sessionsTable.insert(object)

    ################################################
    print("time: " + str(time.time() - start))
    ################################################

    return Response(response=json.dumps({'queryId': object.id}), status=200, headers=utils.COMMON_HEADER_RESPONSE)


@app.route('/articles', methods=['GET'])
def get_articles():
    try:
        (query_id, count, filter_feature, filter_list) = utils.get_query_params('id', 'count', 'filterFeature',
                                                                                'filterList')
    except Response as res:
        return res
    sessions_table_object = sessionsTable.get(query_id)
    articles_df = utils.handle_articles_count(sessions_table_object, count)
    articles_df = utils.filter_articles_by_feature(articles_df, filter_feature, filter_list)
    articles_json = utils.articles_to_json(articles_df)
    return Response(response=json.dumps({"articles": articles_json}), status=200, headers=utils.COMMON_HEADER_RESPONSE)


@app.route('/metadata', methods=['GET'])
def get_metadata():
    try:
        (query_id, count, filter_feature, filter_list) = utils.get_query_params('id', 'count', 'filterFeature',
                                                                                'filterList')
    except Response as res:
        return res
    sessions_table_object = sessionsTable.get(query_id)
    articles_df = utils.handle_articles_count(sessions_table_object, count)
    articles_df = utils.filter_articles_by_feature(articles_df, filter_feature, filter_list)
    metadata = utils.get_metadata(articles_df)
    return {"metadata": metadata}

@app.route('/network', methods=['GET'])
def get_network():
    try:
        (query_id, count, filter_feature, filter_list, feature) = utils.get_query_params('id', 'count', 'filterFeature',
                                                                                'filterList', 'feature')
    except Response as res:
        return res
    sessions_table_object = sessionsTable.get(query_id)
    articles_df = utils.handle_articles_count(sessions_table_object, count)
    articles_df = utils.filter_articles_by_feature(articles_df, filter_feature, filter_list)
    network = Network(articles_df, feature)
    return network.get_network()

@app.route('/getOne', methods=['GET'])
def get_one():
    article_id = utils.get_query_params('id')
    return SemanticScholarAPI.get_one_article(article_id)


@app.route('/categories', methods=['GET'])
def get_categories():
    query_id, count, filter_feature, filter_list = utils.get_query_params('id', 'count', 'filterFeature',
                                                                                'filterList')
    sessions_table_object = sessionsTable.get(query_id)
    articles_df = utils.handle_articles_count(sessions_table_object, count)
    articles_df = utils.filter_articles_by_feature(articles_df, filter_feature, filter_list)
    categories = utils.get_categories(articles_df)
    return {"categories": categories}


if __name__ == '__main__':

    ##################################################################
    # REMOVE REMOVE REMOVE REMOVE REMOVE REMOVE REMOVE REMOVE REMOVE #
    from waitress import serve
    if len(sys.argv) > 1 and sys.argv[1].lower() == 'prod':
        serve(app, host="0.0.0.0", port=int(os.environ.get("PORT", utils.PORT)))
    # REMOVE REMOVE REMOVE REMOVE REMOVE REMOVE REMOVE REMOVE REMOVE #
    ##################################################################
    else:
        app.run(host='0.0.0.0', debug=True, port=int(os.environ.get("PORT", utils.PORT)))
