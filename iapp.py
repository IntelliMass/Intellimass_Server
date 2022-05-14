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


@app.route('/health')
def health_check():
    return "OK"


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
    except Exception as res:
        return eval(str(res))
    raw_articles = SemanticScholarAPI.get_articles(query)
    extended_articles = utils.article_extender(raw_articles, query)
    extended_articles = utils.cluster_articles(extended_articles)
    object = objects.SessionObject(query, extended_articles, config.Defaults.numOfArticles_firstSearch)
    sessionsTable.insert(object)

    ################################################
    print("time: " + str(time.time() - start))
    ################################################

    return Response(response=json.dumps({'queryId': object.id}), status=200, headers=utils.COMMON_HEADER_RESPONSE)


@app.route('/articles', methods=['GET'])
def get_articles():
    """
    Steps:
        1.
    :return:
    """
    try:
        (query_id, count, filters, clusters, num_of_clusters) = utils.get_query_params('id', 'count', 'filters',
                                                                                       'clusters', 'numOfClusters')
    except Exception as res:
        return eval(str(res))
    sessions_table_object = sessionsTable.get(query_id)
    articles_df = utils.handle_articles_count(sessions_table_object, count)
    articles_df = utils.filter_articles_by_features(articles_df, filters, clusters)
    articles_df = utils.cluster_articles(articles_df, num_of_clusters)
    articles_json = utils.articles_to_json(articles_df)
    return Response(response=json.dumps({"articles": articles_json}), status=200, headers=utils.COMMON_HEADER_RESPONSE)


@app.route('/metadata', methods=['GET'])
def get_metadata():
    try:
        (query_id, count, filters, clusters, num_of_clusters) = utils.get_query_params('id', 'count', 'filters', 'clusters', 'numOfClusters')
    except Exception as res:
        return eval(str(res))
    sessions_table_object = sessionsTable.get(query_id)
    articles_df = utils.handle_articles_count(sessions_table_object, count)
    articles_df = utils.filter_articles_by_features(articles_df, filters, clusters)
    articles_df = utils.cluster_articles(articles_df, num_of_clusters)
    metadata = utils.get_metadata(articles_df)
    return {"metadata": metadata}


@app.route('/network', methods=['GET'])
def get_network():
    try:
        (query_id, count, filters, feature, clusters, num_of_clusters) = utils.get_query_params('id', 'count', 'filters', 'feature', 'clusters', 'numOfClusters')
    except Exception as res:
        print(str(res))
        return eval(str(res))
    sessions_table_object = sessionsTable.get(query_id)
    articles_df = utils.handle_articles_count(sessions_table_object, count)
    articles_df = utils.filter_articles_by_features(articles_df, filters, clusters)
    articles_df = utils.cluster_articles(articles_df, num_of_clusters)
    try:
        network = Network(articles_df, feature)
        links_list = network.get_network()
    except ValueError as ve:
        return Response(response=str(ve), status=400, headers=utils.COMMON_HEADER_RESPONSE)
    # articles_df.rename(columns={'paperId': 'id'}, inplace=True)
    articles_json = utils.articles_to_json(articles_df)
    return Response(response=json.dumps({"network": {"nodes": articles_json, "links": links_list}}), status=200, headers=utils.COMMON_HEADER_RESPONSE)


@app.route('/getOne', methods=['GET'])
def get_one():
    article_id = utils.get_query_params('id')
    return SemanticScholarAPI.get_one_article(article_id)


@app.route('/clusters', methods=['GET'])
def get_clusters():
    try:
        (query_id, count, filters, clusters, num_of_clusters) = utils.get_query_params('id', 'count', 'filters', 'clusters', 'numOfClusters')
    except Exception as res:
        return eval(str(res))
    sessions_table_object = sessionsTable.get(query_id)
    articles_df = utils.handle_articles_count(sessions_table_object, count)
    articles_df = utils.filter_articles_by_features(articles_df, filters, clusters)
    articles_df = utils.cluster_articles(articles_df, num_of_clusters)
    clusters = utils.get_clusters(articles_df)
    return {"clusters": clusters}


##############################################################################################
# UPDATE UPDATE UPDATE UPDATE UPDATE UPDATE UPDATE UPDATE UPDATE UPDATE UPDATE UPDATE UPDATE #
##############################################################################################
@app.route('/collections', methods=['GET'])
def get_collections():
    """
    gets collections by user_id
    1 parameter:
        user_id: to get user's collections
    :return: 200/400
    """
    user_id = utils.get_query_params('user_id')
    print(f'user_id: {user_id}')
    private_collection_table_object = privateCollectionsTable.get(user_id, id_var="user_id")
    del private_collection_table_object['_id']
    del private_collection_table_object['user_id']
    del private_collection_table_object['query_id']
    array_of_collections = [private_collection_table_object]
    return {"collection": array_of_collections}


@app.route('/create_collection', methods=['POST'])
def create_collection():
    """
    creates a collection by user id
    3 parameters:
        user_id, collection_name: to create a collection by user id and collection name
        articles_id: list of articles ids to save for the user by collection name
    :return: 200/400
    """
    try:
        user_id, query_id = utils.get_query_params('user_id', 'query_id')
        collection_name = utils.get_post_data('collection_name')
    except Exception as r:
        return Response(eval(str(r)))
    collection_object = objects.PrivateCollectionObject(user_id, collection_name, query_id)
    if privateCollectionsTable.is_collection_exists(user_id, collection_name):
        print('exists')
        return Response(response=json.dumps({'user_id': collection_object.user_id}), status=400,
                        headers=utils.COMMON_HEADER_RESPONSE)
    else:
        print('not exists')
        privateCollectionsTable.insert(collection_object)
        return Response(response=json.dumps({'user_id': collection_object.user_id}), status=200,
                        headers=utils.COMMON_HEADER_RESPONSE)


# @app.route('/update_insert', methods=['PATCH'])
@app.route('/insert_article', methods=['PATCH'])
# def update_insert():
def insert_article():
    """
    insert to existing collection by user an article
    3 parameters:
        user_id, collection_name: to get the needed collection
        article_id: to insert it to the collection
    :return: 200/400
    """
    user_id = utils.get_query_params('user_id')
    collection_name, query_id, article_id = utils.get_post_data('collection_name', 'query_id', 'article_id')
    article_obj = sessionsTable.get_article(query_id, article_id)
    privateCollectionsTable.update({'user_id': user_id, 'collection_name': collection_name},
                                   {'$push': {'articles_list': article_obj}})
    return Response(response=json.dumps({'user_id': user_id}), status=200, headers=utils.COMMON_HEADER_RESPONSE)


@app.route('/update_delete', methods=['PATCH'])
def update_delete():
    """
    deletes article from user's collection
    3 parameters:
        user_id, collection_name: to get the needed collection
        article_id: to delete the article from the collection
    :return: 200/400
    """
    user_id = utils.get_query_params('user_id')

    collection_name, article_id = utils.get_post_data('collection_name', 'article_id')
    privateCollectionsTable.update({'user_id': user_id, 'collection_name': collection_name},
                                   {'$pull': {'articles_id': article_id}})
    return Response(response=json.dumps({'user_id': user_id}), status=200, headers=utils.COMMON_HEADER_RESPONSE)


@app.route('/collection_delete', methods=['DELETE'])
def collection_delete():
    """
    deletes user's collection
    2 parameters:
        user_id, collection_name: to delete user's collection
    :return: 200/400
    """
    user_id = utils.get_query_params('user_id')
    collection_name = utils.get_post_data('collection_name')
    privateCollectionsTable.delete({'user_id': user_id, 'collection_name': collection_name})
    return Response(response=json.dumps({'user_id': user_id}), status=200, headers=utils.COMMON_HEADER_RESPONSE)


@app.route('/rename_collection', methods=['PATCH'])
def collection_rename():
    """
    updates user's collection name
    3 parameters:
        user_id: to locate user's collection
        collection_name, new_collection: to find the collection and replace the name
    :return: 200/400
    """
    user_id = utils.get_query_params('user_id')
    current_collection, new_collection = utils.get_post_data('collection_name', 'new_collection')
    try:
        privateCollectionsTable.replace(user_id, current_collection, new_collection)
    except Exception as r:
        return Response(eval(str(r)))
    return Response(response=json.dumps({'user_id': user_id}), status=200, headers=utils.COMMON_HEADER_RESPONSE)


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
