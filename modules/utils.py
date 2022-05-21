import datetime
from collections import Counter

from flask import request, Response
import json
import math
import pandas as pd
from modules import algorithms
from modules.algorithms.frequentWords import append as append_frequent_words
from modules.db.objects import SessionObject, PrivateCollectionObject
from modules.db import sessionsTable, privateCollectionsTable
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

MAX_COMMON_FEATURE = 10


#####################################################

def roundup(x: int):
    """
    Round up to 100
    """
    return int(math.ceil(x / 100.0)) * 100


def get_post_data(*argv):
    """
    Extract post body by given *argv
    """
    data = []
    for key in argv:
        extractedKey = json.loads(request.data.decode('utf-8')).get(key)
        if key == 'query':
            extractedKey = extractedKey.split('+')
        if extractedKey is None:
            raise Exception(f"Response(response='Bad Request - {key}', status=400, \
                           headers=COMMON_HEADER_RESPONSE)")
        data.append(extractedKey)
    return tuple(data)


def filters_parser(filters: str):
    """
    Extract filters from query separated by %$
    """
    filters = filters.split('%$')
    filters_array = []
    for filter in filters:
        filter = filter.split('=')
        filters_array.append((filter[0], filter[1]))
    return filters_array


def clusters_parser(clusters: str):
    """
    Extract filters from query separated by %$
    """
    if clusters is None or clusters == "":
        return None
    return clusters.split('%$')


def get_query_params(*argv):
    """
    Extract query params from GET request
    """
    data = []
    for key in argv:
        extractedKey = request.args.get(key)
        print(key, extractedKey)
        if key == 'filters' and \
                (extractedKey is None or extractedKey == [] or extractedKey == ""):
            extractedKey = None
        elif key == 'filters':
            extractedKey = filters_parser(extractedKey)
        elif key == 'clusters':
            extractedKey = clusters_parser(extractedKey)
        elif key == 'numOfClusters':
            extractedKey = int(extractedKey) if extractedKey is not None else 4
        elif extractedKey is None or extractedKey == '':
            raise Exception(f"Response(response='Bad Request - {key}', status=400, headers={COMMON_HEADER_RESPONSE})")
        data.append(extractedKey)
    print(data)
    if len(data) == 1:
        return data[0]
    return tuple(data)


def clean_articles_df(articles_df: pd.DataFrame):
    """
    CLean articles DF:
        * Faulted abstract
    """
    articles_df.dropna(subset=["abstract"], inplace=True)
    return articles_df


def article_extender(articles_df: pd.DataFrame, query: str):
    """
    Extend articles DataFrame with frequent words & clusters (topics)
    """
    articles_df = clean_articles_df(articles_df)
    articles_df = append_frequent_words(articles_df, query)
    return articles_df


def cluster_articles(articles_df: pd.DataFrame, session_obj: dict, num_of_clusters=4):
    """
    Use K-Means clustering algorithm & NLP's LDA algorithm for give for each cluster unique name
    """
    print('cluster' in articles_df.columns)
    if 'cluster' in articles_df.columns:
        print(len(set(articles_df['cluster'])) == num_of_clusters)
    if 'cluster' in articles_df.columns and len(set(articles_df['cluster'])) == num_of_clusters:
        return articles_df
    search_keys_list = session_obj['query'].split() if type(session_obj['query']) == type(str) else session_obj['query']
    lda_modeling = algorithms.kmeans_lda.LdaModeling(articles_df, search_keys_list, num_of_clusters)
    articles_df = lda_modeling.papers
    return articles_df


def handle_articles_count(session_object: dict, count: int):
    """
    Return articles DataFrame by given count,
    if count bigger than articles exist app will extend the articles DataFrame.
    """
    count = int(count)
    articles_df = pd.DataFrame(session_object["articles"])
    if count > len(articles_df):
        new_articles_df = SemanticScholarAPI.get_articles(articles_df, offset=session_object["offset"])
        articles_df.append(new_articles_df, ignore_index=True)
        articles_df = article_extender(articles_df, session_object["query"])
        sessionsTable.update(session_object["id"], session_object)
    return articles_df[:count]


def filter_articles_by_features(articles_df: pd.DataFrame, filters: list, clusters: list):
    """
    Filter articles DataFrame by list of filters,
    filters contains tuples of (filter feature, filter)
    """
    if (filters is None or filters == []) and (clusters is None or clusters == []):
        return articles_df

    if filters is None:
        filters = []

    if clusters is None:
        clusters = []

    print(f"filters: {filters}\nclusters: {clusters}")
    clusters = ('cluster', clusters)
    filters = filters.append(clusters) if filters != [] else [clusters]

    def common_filter(row, filter_feature, filter):
        return filter in row[filter_feature]

    def filter_authors(row, author):
        return author in [author['name'] for author in row['authors']]

    # print(clusters)
    # counter = 0
    # for _, article in articles_df.iterrows():
    #     if article['cluster'] in clusters[1]:
    #         counter += 1
    # print(f"len df {len(articles_df)}")
    # print(f"Counter {counter}")
    # pd.set_option("display.max_rows", None, "display.max_columns", None)
    # print(articles_df['cluster'])

    for filter_feature, filter in filters:
        if filter_feature.lower() == 'authors':
            articles_df = articles_df[articles_df.apply(filter_authors, axis=1, args=(filter,))]
        if filter_feature == 'cluster':
            print(filter)
            articles_df = articles_df[articles_df['cluster'].isin(filter)]
        else:
            articles_df = articles_df[articles_df.apply(common_filter, axis=1, args=(filter_feature, filter))]

    return articles_df


def articles_to_json(articles_df: pd.DataFrame):
    """
    Return article objects list
    """
    return articles_df.to_dict('records')


def get_metadata(articles_df: pd.DataFrame):
    frequent_words_counter = []
    authors_counter = []
    fields_of_study_counter = []
    years_counter = []
    for _, article in articles_df.iterrows():
        frequent_words_counter.extend([frequent_word for frequent_word in article['frequentWords']])
        authors_counter.extend([author['name'] for author in article['authors']])
        fields_of_study_counter.extend(article['fieldsOfStudy'] if article['fieldsOfStudy'] is not None else [])
        years_counter.append(article['year'])

    most_common_frequent_words = dict(Counter(frequent_words_counter))
    most_common_frequent_words = [{"title": k if k[0].isupper() else k.capitalize(), "rank": v} for k, v in
                                  sorted(most_common_frequent_words.items(), key=lambda item: item[1], reverse=True)[
                                  :MAX_COMMON_FEATURE]]

    most_common_fields_of_study = dict(Counter(fields_of_study_counter))
    most_common_fields_of_study = [{"title": k, "rank": v} for k, v in sorted(most_common_fields_of_study.items(),
                                                                     key=lambda item: item[1], reverse=True)[
                                                              :MAX_COMMON_FEATURE]]

    most_common_years = dict(Counter(years_counter))
    most_common_years = [{"title": k, "rank": v} for k, v in sorted(most_common_years.items(),
                                                                    key=lambda item: item[1], reverse=True)[
                                                             :MAX_COMMON_FEATURE]]

    most_common_authors = dict(Counter(authors_counter))
    most_common_authors = [{"title": k, "rank": v} for k, v in sorted(most_common_authors.items(),
                                                                      key=lambda item: item[1], reverse=True)[
                                                               :MAX_COMMON_FEATURE]]
    return {
        "common_words": most_common_frequent_words,
        "fields_of_study": most_common_fields_of_study,
        "years": most_common_years,
        "authors": most_common_authors,
        "topics": []
    }


def get_clusters(articles_df: pd.DataFrame):
    clusters = articles_df['cluster'].value_counts().to_dict()
    pd.set_option("display.max_rows", None, "display.max_columns", None)
    print(articles_df['cluster'])
    print(clusters)
    res = [{"title": title, "rank": value} for title, value in clusters.items()]
    return res


def collection_to_json(private_collection_object: pd.DataFrame):
    return private_collection_object.to_dict('collection_name')


def extract_articles_from_session_db(sessions_table_object: SessionObject, article_list: list):
    articles = sessions_table_object.articles
    return articles[articles['id'].isin(article_list)]


def get_all_user_collections(user_id: str):
    private_collection_table_object = privateCollectionsTable.get(user_id, id_var="user_id")
    if isinstance(private_collection_table_object, list):
        for i_article in private_collection_table_object:
            if "_id" in i_article:
                del i_article['_id']
            if "user_id" in i_article:
                del i_article['user_id']
    else:
        if "_id" in private_collection_table_object:
            del private_collection_table_object['_id']
        if "user_id" in private_collection_table_object:
            del private_collection_table_object['user_id']
        private_collection_table_object = [private_collection_table_object]
    return {"collection": private_collection_table_object}


def generate_breadcrumb(breadcrumbs: list, query_list: list, clusters: list, meta_data_list: list, count: int):

    print(f"query: {query_list}, type: {type(query_list)}")
    if isinstance(query_list, str):
        query_list = [query_list]

    if clusters is None:
        clusters = []

    if meta_data_list is None:
        meta_data_list = []

    print(clusters)
    print(meta_data_list)

    count = int(count)

    if breadcrumbs is None or breadcrumbs == []:
        breadcrumbs = [{
            "index": 0,
            "time": datetime.datetime.now().strftime("%d/%m/%Y | %H:%M:%S"),
            "queryList": query_list,
            "clusters": clusters,
            "metadataList": meta_data_list,
            "count": count
        }]
        return breadcrumbs

    new_breadcrumb = {
        "queryList": breadcrumbs[-1]["queryList"],
        "clusters": clusters,
        "metadataList": meta_data_list,
        "count": count
    }

    if new_breadcrumb != breadcrumbs[-1]:
        new_breadcrumb['index'] = breadcrumbs[-1]['index']
        new_breadcrumb['time'] = datetime.datetime.now().strftime("%d/%m/%Y | %H:%M:%S")
        breadcrumbs.append(breadcrumbs)

    return breadcrumbs


def update_breadcrumbs(sessions_table_object: dict, count: int, filters: list, clusters: list):
    pass
    # sessions_table_object['breadcrumbs'] = generate_breadcrumb(sessions_table_object['breadcrumbs'], sessions_table_object['query'], filters, clusters, count)
    # session_new_object = SessionObject(sessions_table_object['query'], sessions_table_object['articles'], sessions_table_object['offset'],
    #               sessions_table_object["id"], sessions_table_object['breadcrumbs'])
    # sessionsTable.update(sessions_table_object["id"], session_new_object)


def get_breadcrumbs(query_id: str):

    return [{
            "index": 0,
            "time": "2015-09-01 | 14:32:15",
            "queryList": ["cyber", "IOT"],
            "clusters": ["Systems", "Software", "Network"],
            "metadataList": ["2020", "Remy Martiti"],
            "count": 100
        },
        {
            "index": 1,
            "time": "2015-09-01 | 14:32:17",
            "queryList": ["cyber"],
            "clusters": ["Systems", "Software", "Network"],
            "metadataList": ["2020", "Remy Martiti"],
            "count": 100
        },
        {
            "index": 2,
            "time": "2015-09-01 | 14:32:19",
            "queryList": ["cyber", "IOT"],
            "clusters": ["Systems", "Network"],
            "metadataList": ["2020", "Remy Martiti"],
            "count": 100
        },]

    sessions_table_object = sessionsTable.get(query_id)
    return sessions_table_object['breadcrumbs']