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
        if extractedKey is None:
            raise Exception(f"Response(response='Bad Request - {key}', status=400, \
                           headers=COMMON_HEADER_RESPONSE)")
        data.append(extractedKey)
    return tuple(data)


def filters_parser(filters: str):
    """
    Extract filters from query separated by %%
    """
    filters = filters.split('%%')
    filters_array = []
    for filter in filters:
        filter = filter.split('=')
        filters_array.append((filter[0], filter[1]))
    return filters_array


def clusters_parser(clusters: str):
    """
    Extract filters from query separated by %%
    """
    if clusters is None or clusters == "":
        return None
    return clusters.split('%%')


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
            extractedKey = int(extractedKey)
        elif extractedKey is None or extractedKey == '':
            raise Exception(f"response='Bad Request - {key}', status=400, \
                            headers={'Access-Control-Allow-Origin': '*'}")
        data.append(extractedKey)
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


def cluster_articles(articles_df: pd.DataFrame, num_of_clusters=4):
    """
    Use K-Means clustering algorithm & NLP's LDA algorithm for give for each cluster unique name
    """
    lda_modeling = algorithms.kmeans_lda.LdaModeling(articles_df, num_of_clusters)
    articles_df = lda_modeling.papers
    return articles_df


def handle_articles_count(session_object: dict, count: int):
    """
    Return articles DataFrame by given count,
    if count bigger than articles exist app will extend the articles DataFrame.
    """
    count = int(count)
    session_object["articles"] = pd.DataFrame(session_object["articles"])
    if count > len(session_object["articles"]):
        new_articles_df = SemanticScholarAPI.get_articles(session_object["query"], offset=session_object.offset)
        session_object["articles"].append(new_articles_df, ignore_index=True)
        session_object["articles"] = article_extender(session_object["articles"], session_object["query"])
        sessionsTable.update(session_object["id"], session_object)
    return session_object["articles"][:count]


def filter_articles_by_features(articles_df: pd.DataFrame, filters: list, clusters: list):
    """
    Filter articles DataFrame by list of filters,
    filters contains tuples of (filter feature, filter)
    """
    if (filters is None or filters == []) and (clusters is None or clusters == []):
        return articles_df



    print(f"filters: {filters}\nclusters: {clusters}")

    def common_filter(row, filter_feature, filter):
        return filter in row[filter_feature]

    def filter_authors(row, author):
        return author in [author['name'] for author in row['authors']]

    for filter_feature, filter in filters:
        if filter_feature.lower() == 'authors':
            articles_df = articles_df[articles_df.apply(filter_authors, axis=1, args=(filter,))]
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
    # clusters = list(set((articles_df['cluster'])))
    clusters = articles_df['cluster'].value_counts().to_dict()
    res = [{"title": title, "rank": value} for title, value in clusters.items()]
    return res

def collection_to_json(private_collection_object: pd.DataFrame):
    return private_collection_object.to_dict('collection_name')


def extract_articles_from_session_db(sessions_table_object: SessionObject, article_list: list):
    articles = sessions_table_object.articles
    return articles[articles['id'].isin(article_list)]