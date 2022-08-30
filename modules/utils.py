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
                           headers={COMMON_HEADER_RESPONSE})")
        data.append(extractedKey)
    return tuple(data)


def query_handler(query):
    print(query)
    tmp_query = []
    for qu in query:
        tmp_query.append(qu.strip())


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
        print(key, extractedKey, type(extractedKey))
        if key == 'filters' and \
                (extractedKey is None or extractedKey == [] or extractedKey == ""):
            extractedKey = None
        elif key == 'filters':
            extractedKey = filters_parser(extractedKey)
        elif key == 'clusters':
            if "[object Object]" in extractedKey:
                raise Exception(
                    f"Response(response='Bad Request - {key}', status=400, headers={COMMON_HEADER_RESPONSE})")
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
    if 'level_0' in articles_df.columns:
        articles_df.drop(['level_0'], axis=1, inplace=True)
    articles_df.reset_index(inplace=True)
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
    if 'cluster' in articles_df.columns and len(set(articles_df['cluster'])) == num_of_clusters:
        return articles_df
    search_keys_list = session_obj['query'].split() if type(session_obj['query']) == type(str) else session_obj['query']
    re_flag = False
    for i in range(10):
        lda_modeling = algorithms.kmeans_lda.LdaModeling(articles_df, search_keys_list, num_of_clusters, re_flag)
        articles_df = lda_modeling.papers
        print(f"Clusters: {set(articles_df['cluster'])} num_of_clusters: {num_of_clusters}")
        for cluster in articles_df['cluster']:
            if type(cluster) == type(int):
                re_flag = True
                continue
        if (len(set(articles_df['cluster'])) == num_of_clusters):
            break
        re_flag = True
    if (len(set(articles_df['cluster'])) != num_of_clusters):
        raise RuntimeError("clusters.length != numOfClusters")
    return articles_df


def handle_articles_count(session_object: dict, count: int):
    """
    Return articles DataFrame by given count,
    if count bigger than articles exist app will extend the articles DataFrame.
    """
    count = int(count)
    articles_df = pd.DataFrame(session_object["articles"])
    if count > len(articles_df):
        new_articles_df = SemanticScholarAPI.get_articles(session_object['query'],
                                                operator=session_object["operator"], offset=session_object["offset"])
        articles_df = articles_df.append(new_articles_df, ignore_index=True)
        articles_df = article_extender(articles_df, session_object["query"])
        articles_df['queryId'] = articles_df['queryId'].fillna(articles_df['queryId'][0])
        session_object['articles'] = articles_df.to_dict('records')
        session_object['offset'] += 200
        sessionsTable.update(session_object["id"], session_object)
    return articles_df[:count]


def filter_articles_by_features(articles_df: pd.DataFrame, filters: list, clusters: list):
    """
    Filter articles DataFrame by list of filters,
    filters contains tuples of (filter feature, filter)
    """
    print(f"typeof filters {type(filters)} typeof clusters {type(filters)}")
    if (filters is None or filters == []) and (clusters is None or clusters == []):
        return articles_df

    filters = [] if filters is None else filters
    clusters = [] if clusters is None else clusters

    print(f"filters: {filters}\nclusters: {clusters}")

    print(f"columns: {articles_df.columns}")

    def common_filter(row, filter_feature, filter):
        if filter_feature not in row or row[filter_feature] is None:
            return False
        return filter.lower() in [string.lower() for string in row[filter_feature]]


    def filter_authors(row, author):
        return author in [author['name'] for author in row['authors']]

    def filter_topics(row, topic):
        return topic in [topic['topic'] for topic in row['topics']]

    new_articles_df = pd.DataFrame()
    for filter_feature, filter in filters:

        if filter_feature.lower() == 'topics':
            new_articles_df = new_articles_df.append(articles_df[articles_df.apply(filter_topics, axis=1, args=(filter,))],
                                   ignore_index=True)
        elif filter_feature.lower() == 'authors':
            new_articles_df = new_articles_df.append(articles_df[articles_df.apply(filter_authors, axis=1, args=(filter,))],
                                   ignore_index=True)

        elif filter_feature == 'year':
            new_articles_df = new_articles_df.append(articles_df[articles_df['year'] == int(filter)], ignore_index=True)

        else:
            temp = articles_df[articles_df.apply(common_filter, axis=1, args=(filter_feature, filter))]
            new_articles_df = new_articles_df.append(temp, ignore_index=True)

    if len(new_articles_df) == 0:
        new_articles_df = articles_df

    if clusters is not None and clusters != []:
        new_articles_df = new_articles_df[new_articles_df['cluster'].isin(clusters)]

    new_articles_df = new_articles_df.drop_duplicates(subset='title', ignore_index=True)
    return new_articles_df


def articles_to_json(articles_df: pd.DataFrame):
    """
    Return article objects list
    """
    articles_df.drop(["index"], axis=1, inplace=True)
    return articles_df.to_dict('records')


def get_metadata(articles_df: pd.DataFrame):
    frequent_words_counter = []
    authors_counter = []
    fields_of_study_counter = []
    years_counter = []
    topics_counter = []
    for _, article in articles_df.iterrows():
        topics_counter.extend([topicName['topic'] for topicName in article['topics']])
        frequent_words_counter.extend([frequent_word.lower() for frequent_word in article['frequentWords']])
        authors_counter.extend([author['name'] for author in article['authors']])
        fields_of_study_counter.extend(article['fieldsOfStudy'] if article['fieldsOfStudy'] is not None else [])
        years_counter.append(article['year'])

    most_common_topics = dict(Counter(topics_counter))
    most_common_topics = [{"title": k , "rank": v} for k, v in sorted(most_common_topics.items(),
                                    key=lambda item: item[1], reverse=True)[:MAX_COMMON_FEATURE]]

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
        "topics": most_common_topics
    }


def get_clusters(articles_df: pd.DataFrame):
    clusters = articles_df['cluster'].value_counts().to_dict()
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

    meta_data_list = [{"type": meta_data[0], "title": meta_data[1]} for meta_data in meta_data_list]

    print(clusters)
    print(meta_data_list)

    count = int(count)

    timestamp = (datetime.datetime.now() + datetime.timedelta(hours=3)).strftime("%d/%m/%Y | %H:%M:%S")

    if breadcrumbs is None or breadcrumbs == []:
        breadcrumbs = [{
            "index": 0,
            "time": timestamp,
            "queryList": query_list,
            "clusters": clusters,
            "metadataList": meta_data_list,
            "count": count
        }]
        return breadcrumbs

    new_breadcrumb = {
        "queryList": query_list,
        "clusters": clusters,
        "metadataList": meta_data_list,
        "count": count
    }

    t_breadcrumb = {
        "queryList": breadcrumbs[-1]['queryList'],
        "clusters": breadcrumbs[-1]['clusters'],
        "metadataList": breadcrumbs[-1]['metadataList'],
        "count": breadcrumbs[-1]['count']
    }

    if new_breadcrumb != t_breadcrumb:
        new_breadcrumb['index'] = breadcrumbs[-1]['index'] + 1
        new_breadcrumb['time'] = timestamp
        breadcrumbs.append(new_breadcrumb)

    return breadcrumbs


def update_breadcrumbs(sessions_table_object: dict, count: int, filters: list, clusters: list):
    t_breadcrumbs = generate_breadcrumb(sessions_table_object['breadcrumbs'], sessions_table_object['query'], clusters, filters, count)
    if t_breadcrumbs is not None:
        print(t_breadcrumbs)
        session_new_object = SessionObject(sessions_table_object['query'], sessions_table_object['operator'], sessions_table_object['articles'], sessions_table_object['offset'], sessions_table_object["id"], t_breadcrumbs, sessions_table_object['iteration'], sessions_table_object['iteration_cache'])
        sessionsTable.update(session_new_object.id, session_new_object.__dict__)


def get_breadcrumbs(query_id: str):
    sessions_table_object = sessionsTable.get(query_id)
    return sessions_table_object['breadcrumbs']


def search_word_in_abstract(word: str, articles_df: pd.DataFrame):
    articles_filtered_by_word = articles_df[articles_df['abstract'].str.contains(word)]
    return articles_filtered_by_word


def handle_new_iteration(sessions_table_object, filters, clusters):
    clusters = list(clusters)
    clusters = [cluster['title'] for cluster in clusters]
    filters = list(filters)
    count = sessions_table_object['breadcrumbs'][-1]['count']
    articles_df = pd.DataFrame(sessions_table_object['articles'][:count])
    new_articles_df = filter_articles_by_features(articles_df, filters, clusters)
    sessions_table_object['iteration'] += 1
    sessions_table_object['iteration_cache'] = sessions_table_object['iteration_cache'].append(articles_df.to_dict('records')) if not None else [articles_df.to_dict('records')]
    sessions_table_object['articles'] = new_articles_df.to_dict('records')
    return sessions_table_object


def set_iter(sessions_table_object, iter_num):
    pass

