import os
from flask import Flask, Response
from flask_cors import CORS
import time
import json
import datetime
import traceback

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
        (query, operator) = utils.get_post_data('query', 'operator')
    except Exception as res:
        return eval(str(res))
    raw_articles = SemanticScholarAPI.get_articles(query, operator)
    extended_articles = utils.article_extender(raw_articles, query)
    sessions_table_object = objects.SessionObject(query, operator).__dict__
    extended_articles = utils.cluster_articles(extended_articles, sessions_table_object)
    object = objects.SessionObject(query, operator, extended_articles, config.Defaults.numOfArticles_firstSearch)
    print(object.breadcrumbs)
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
        try:
            (query_id, count, filters, clusters, num_of_clusters) = utils.get_query_params('id', 'count', 'filters',
                                                                                           'clusters', 'numOfClusters')
        except Exception as res:
            return str(res)
        sessions_table_object = sessionsTable.get(query_id)
        articles_df = utils.handle_articles_count(sessions_table_object, count)
        print(f"len articles after count: {len(articles_df)}")
        articles_df = utils.filter_articles_by_features(articles_df, filters, clusters)
        print(f"len articles after filter: {len(articles_df)}")
        try:
            articles_df = utils.cluster_articles(articles_df, sessions_table_object, num_of_clusters)
        except (ValueError, KeyError):
            return Response(response=json.dumps({"articles": []}), status=400, headers=utils.COMMON_HEADER_RESPONSE)
        print(f"len articles after cluster: {len(articles_df)}")
        utils.update_breadcrumbs(sessions_table_object, count, filters, clusters)
        articles_json = utils.articles_to_json(articles_df)
        print(f"len articles: {len(articles_json)}")
        return Response(response=json.dumps({"articles": articles_json}), status=200, headers=utils.COMMON_HEADER_RESPONSE)
    except:
        print(traceback.format_exc())
        return Response(response=json.dumps({"articles": []}), status=200, headers=utils.COMMON_HEADER_RESPONSE)


@app.route('/word_search', methods=['GET'])
def get_search():
    (query_id, count, filters, clusters, num_of_clusters, search_word) = utils.get_query_params('id', 'count', 'filters'
                                                                                                , 'clusters',
                                                                                                'numOfClusters',
                                                                                                'searchWord')
    sessions_table_object = sessionsTable.get(query_id)
    articles_df = utils.handle_articles_count(sessions_table_object, count)
    articles_df = utils.filter_articles_by_features(articles_df, filters, clusters)
    articles_df = utils.search_word_in_abstract(search_word, articles_df)
    print(f'Length of dataframe after search filter {len(articles_df)}')
    articles_json = utils.articles_to_json(articles_df)
    return json.dumps({"articles": articles_json})


@app.route('/metadata', methods=['GET'])
def get_metadata():
    try:
        (query_id, count, filters, clusters, num_of_clusters) = utils.get_query_params('id', 'count', 'filters', 'clusters', 'numOfClusters')
    except Exception as res:
        return eval(str(res))
    sessions_table_object = sessionsTable.get(query_id)
    articles_df = utils.handle_articles_count(sessions_table_object, count)
    articles_df = utils.filter_articles_by_features(articles_df, filters, clusters)
    try:
        articles_df = utils.cluster_articles(articles_df, sessions_table_object, num_of_clusters)
    except (ValueError, KeyError):
        return Response(response=json.dumps({"articles": []}), status=400, headers=utils.COMMON_HEADER_RESPONSE)
    metadata = utils.get_metadata(articles_df)
    return {"metadata": metadata}


@app.route('/network', methods=['GET'])
def get_network():
    try:
        (query_id, count, filters, feature, clusters, num_of_clusters) = utils.get_query_params('id', 'count', 'filters', 'feature', 'clusters', 'numOfClusters')
    except Exception as res:
        return eval(str(res))
    sessions_table_object = sessionsTable.get(query_id)
    articles_df = utils.handle_articles_count(sessions_table_object, count)
    articles_df = utils.filter_articles_by_features(articles_df, filters, clusters)
    articles_df = utils.cluster_articles(articles_df, sessions_table_object, num_of_clusters)
    try:
        network = Network(articles_df, feature)
        articles_df, links_list = network.get_network()
    except ValueError as ve:
        return Response(response=str(ve), status=400, headers=utils.COMMON_HEADER_RESPONSE)
    articles_json = utils.articles_to_json(articles_df)
    return Response(response=json.dumps({"network": {"nodes": articles_json, "links": links_list}}), status=200, headers=utils.COMMON_HEADER_RESPONSE)


@app.route('/getOne', methods=['GET'])
def get_one():
    article_id, query_id = utils.get_query_params('id', 'query_id')
    article = SemanticScholarAPI.get_one_article(article_id)
    articles_obj = sessionsTable.get_article_paperid(query_id, article_id)
    temp_article = json.loads(article)
    print(f'temp_article {temp_article}')
    temp_article['frequentWords'] = articles_obj['articles'][0]['frequentWords']
    temp_article['cluster'] = articles_obj['articles'][0]['cluster']
    temp_article['query_word'] = articles_obj['query']
    article = json.dumps(temp_article)
    return article


@app.route('/clusters', methods=['GET'])
def get_clusters():
    try:
        (query_id, count, filters, clusters, num_of_clusters) = utils.get_query_params('id', 'count', 'filters', 'clusters', 'numOfClusters')
    except Exception as res:
        return eval(str(res))
    sessions_table_object = sessionsTable.get(query_id)
    articles_df = utils.handle_articles_count(sessions_table_object, count)
    articles_df = utils.filter_articles_by_features(articles_df, filters, clusters)
    articles_df = utils.cluster_articles(articles_df, sessions_table_object, num_of_clusters)
    clusters = utils.get_clusters(articles_df)
    print(clusters)
    return {"clusters": clusters}


# works and integrated
@app.route('/collections', methods=['GET'])
def get_collections():
    """
    gets collections by user_id
    1 parameter:
        user_id: to get user's collections
    :return: 200/400
    """
    user_id = utils.get_query_params('user_id')
    print(f'get_collection -> user_id: {user_id}')
    return utils.get_all_user_collections(user_id)


# works and integrated
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
        user_id = utils.get_query_params('user_id')
        collection_name = utils.get_post_data('collection_name')[0]
        print(f'collection_name {collection_name}')
    except Exception as r:
        return Response(eval(str(r)))
    if privateCollectionsTable.is_collection_exists(user_id, collection_name):
        print('exists')
        return Response(response=json.dumps({'user_id': user_id}), status=400,
                        headers=utils.COMMON_HEADER_RESPONSE)
    else:
        print('creating collection')
        collection_object = objects.PrivateCollectionObject(user_id, collection_name)
        print(f'collection_object: {collection_object.user_id}, {collection_object.collection_name}, {collection_object.articles_list}')
        privateCollectionsTable.insert(collection_object)
        return utils.get_all_user_collections(user_id)
        # return Response(response=json.dumps({'user_id': collection_object.user_id, 'status': 200}), status=200,
        #                 headers=utils.COMMON_HEADER_RESPONSE)


# works and integrated
@app.route('/insert_article', methods=['POST'])
def insert_article():
    """
    insert to existing collection by user an article
    3 parameters:
        user_id, collection_name: to get the needed collection
        article_id: to insert it to the collection
    :return: 200/400
    """
    user_id, query_id = utils.get_query_params('user_id', 'query_id')
    collection_name, article_id = utils.get_post_data('collection_name', 'article_id')
    print(f'collection_name: {collection_name}, article_id: {article_id}')
    articles_obj = sessionsTable.get_article_paperid(query_id, article_id)
    articles_obj['articles'][0]['query_word'] = articles_obj['query']
    articles_obj['articles'][0]['timestamp'] = datetime.datetime.now().strftime("%d/%m/%Y | %H:%M:%S")
    print(f'articles_obj: {articles_obj}')
    privateCollectionsTable.update_paper(user_id, collection_name, articles_obj['articles'][0])
    # return Response(response=json.dumps({'user_id': user_id}), status=200, headers=utils.COMMON_HEADER_RESPONSE)
    return utils.get_all_user_collections(user_id)


# works and integrated
@app.route('/pop_article', methods=['POST'])
def pop_article():
    """
    deletes article from user's collection
    3 parameters:
        user_id, collection_name: to get the needed collection
        article_id: to delete the article from the collection
    :return: 200/400
    """
    user_id = utils.get_query_params('user_id')
    collection_name, article_id = utils.get_post_data('collection_name', 'article_id')
    print(f'collection_name: {collection_name}, article_id: {article_id}')
    privateCollectionsTable.pop_paper(user_id, collection_name, article_id)
    # return Response(response=json.dumps({'user_id': user_id}), status=200, headers=utils.COMMON_HEADER_RESPONSE)
    return utils.get_all_user_collections(user_id)


# works and integrated
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
    collection_name = str(collection_name[0])
    print(f'collection_name: {collection_name}')
    privateCollectionsTable.delete_collection(user_id, collection_name)
    # return Response(response=json.dumps({'user_id': user_id}), status=200, headers=utils.COMMON_HEADER_RESPONSE)
    return utils.get_all_user_collections(user_id)


# WORKS, and integrated
@app.route('/rename_collection', methods=['POST'])
def collection_rename():
    """
    updates user's collection name
    3 parameters:
        user_id: to locate user's collection
        collection_name, new_collection: to find the collection and replace the name
    :return: 200/400
    """
    user_id = utils.get_query_params('user_id')
    try:
        (current_collection, new_collection) = utils.get_post_data('collection_name', 'new_collection')
    except Exception as res:
        return eval(str(res))
    # current_collection, new_collection = utils.get_post_data('collection_name', 'new_collection')
    privateCollectionsTable.replace(user_id, current_collection, new_collection)
    # return Response(response=json.dumps({'user_id': user_id}), status=200, headers=utils.COMMON_HEADER_RESPONSE)
    return utils.get_all_user_collections(user_id)


@app.route('/breadcrumbs', methods=['GET'])
def get_breadcrumbs():
    """

    """
    query_id = utils.get_query_params('id')
    breadcrumbs = utils.get_breadcrumbs(query_id)
    return Response(response=json.dumps({"breadCrumbList": breadcrumbs}), status=200, headers=utils.COMMON_HEADER_RESPONSE)


    query_id = utils.get_query_params('id')

    import datetime

    timest = datetime.datetime.now().strftime("%d/%m/%Y | %H:%M:%S")
    mock_breadcrumbs = [
        {
            "index": 0,
            "time": timest,
            "queryList": ["cyber", "IOT"],
            "clusters": ["Systems", "Software", "Network"],
            "metadataList": [{"type": "year", "title": "2020"} , {"type": "authors", "title": "Remy Martiti"}],
            "count": 100
        },
        {
            "index": 1,
            "time": timest,
            "queryList": ["cyber"],
            "clusters": ["Systems", "Software", "Network"],
            "metadataList": [{"type": "year", "title": "2020"} , {"type": "authors", "title": "Remy Martiti"}],
            "count": 100
        },
        {
            "index": 2,
            "time": timest,
            "queryList": ["cyber", "IOT"],
            "clusters": ["Systems", "Network"],
            "metadataList": [{"type": "year", "title": "2020"} , {"type": "authors", "title": "Remy Martiti"}],
            "count": 100
        },
        {
            "index": 3,
            "time": timest,
            "queryList": ["cyber", "IOT"],
            "clusters": ["Systems", "Software", "Network"],
            "metadataList": [{"type": "year", "title": "2020"} , {"type": "authors", "title": "Remy Martiti"}],
            "count": 100
        }
    ]
    return {"breadCrumbList": mock_breadcrumbs}

if __name__ == '__main__':

    ##################################################################
    # REMOVE REMOVE REMOVE REMOVE REMOVE REMOVE REMOVE REMOVE REMOVE #
    # from waitress import serve
    # if len(sys.argv) > 1 and sys.argv[1].lower() == 'prod':
    #     serve(app, host="0.0.0.0", port=int(os.environ.get("PORT", utils.PORT)))
    # REMOVE REMOVE REMOVE REMOVE REMOVE REMOVE REMOVE REMOVE REMOVE #
    ##################################################################
    # else:
    app.run(host='0.0.0.0', debug=True, port=int(os.environ.get("PORT", utils.PORT)))
