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
    query = utils.get_post_data('query')
    extendedArticles = utils.article_extender(rawArticles, query)
    object = objects.SessionObject(query, extendedArticles, config.Defaults.numOfArticles_firstSearch)
    sessionsTable.insert(object)

    ################################################
    print("time: " + str(time.time() - start))
    ################################################

    return Response(response=json.dumps({'queryId': object.id}), status=200, headers=utils.COMMON_HEADER_RESPONSE)


@app.route('/articles', methods=['GET'])
def get_articles():
    query_id, count, filter_feature, filter_list = utils.get_query_params('id', 'count', 'filterFeature', 'filterList')
    sessions_table_object = sessionsTable.get(query_id)
    articles_df = utils.handle_articles_count(sessions_table_object, count)
    articles_df = utils.filter_articles_by_feature(articles_df, filter_feature, filter_list)
    articles_json = utils.articles_to_json(articles_df)
    return {"articles": articles_json}


@app.route('/metadata', methods=['GET'])
def get_metadata():
    query_id, count = utils.get_query_params('id', 'count', 'filterFeature', 'filterList')
    sessions_table_object = sessionsTable.get(query_id)
    articles_df = utils.handle_articles_count(sessions_table_object, count)


@app.route('/network', methods=['GET'])
def get_network():
    pass


@app.route('/getOne', methods=['GET'])
def get_one():
    pass


@app.route('/categories', methods=['GET'])
def get_categories():
    pass


@app.route('/collections', methods=['GET'])
def get_collections():
    """
    gets collections by user_id
    1 parameter:
        user_id: to get user's collections
    :return: 200/400
    """
    user_id = utils.get_query_params('user_id')
    private_collection_table_object = privateCollectionsTable.get(user_id)
    collection_json = utils.collection_to_json(private_collection_table_object)
    return {"collection": collection_json}


@app.route('/create_collection', methods=['POST'])
def create_collection():
    """
    creates a collection by user id
    3 parameters:
        user_id, collection_name: to create a collection by user id and collection name
        articles_id: list of articles ids to save for the user by collection name
    :return: 200/400
    """
    user_id = utils.get_query_params('user_id')
    collection_name, articles_id_list = utils.get_post_data('collection_name', 'articles_id')
    collection_object = objects.PrivateCollectionObject(user_id, collection_name, articles_id_list)
    privateCollectionsTable.insert(collection_object)

    return Response(response=json.dumps({'user_id': collection_object.user_id}), status=200,
                    headers=utils.COMMON_HEADER_RESPONSE)


@app.route('/update_insert', methods=['PATCH'])
def update_insert():
    """
    insert to existing collection by user an article
    3 parameters:
        user_id, collection_name: to get the needed collection
        article_id: to insert it to the collection
    :return: 200/400
    """
    user_id = utils.get_query_params('user_id')
    collection_name, article_id = utils.get_post_data('collection_name', 'article_id')
    privateCollectionsTable.update({'user_id': user_id, 'collection_name': collection_name},
                                   {'$push': {'articles_id': article_id}})
    return Response(response=json.dumps({'user_id': user_id}), status=200, headers=utils.COMMON_HEADER_RESPONSE)


@app.route('/update_delete', method=['PATCH'])
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


@app.route('/collection_delete', method=['DELETE'])
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
