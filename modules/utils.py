from collections import Counter

from flask import request, Response
import json
import math
import pandas as pd
from modules import algorithms
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
    :param argv: Keys to extract from post body
    :return: Post Data -> tuple
    """
    data = []
    for key in argv:
        extractedKey = json.loads(request.data.decode('utf-8')).get(key)
        if extractedKey is None:
            raise Exception(f"Response(response='Bad Request - {key}', status=400, \
                           headers=COMMON_HEADER_RESPONSE)")
        data.append(extractedKey)
    return tuple(data)


def get_query_params(*argv):
    """
    Extract query params from GET request
    """
    data = []
    for key in argv:
        extractedKey = request.args.get(key)
        if (key == 'filterFeature' or key == 'filterList') and \
                (extractedKey is None or extractedKey == [] or extractedKey == ""):
            data.append(None)
            continue
        if extractedKey is None:
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
    articles_df = algorithms.frequentWords.append(articles_df, query)
    articles_df = algorithms.kmeans_lda.LdaModeling(articles_df).papers
    return articles_df


def handle_articles_count(session_object: dict, count: int):
    count = int(count)
    session_object["articles"] = pd.DataFrame(session_object["articles"])
    if count > len(session_object["articles"]):
        new_articles_df = SemanticScholarAPI.get_articles(session_object["query"], offset=session_object.offset)
        session_object["articles"].append(new_articles_df, ignore_index=True)
        session_object["articles"] = article_extender(session_object["articles"], session_object["query"])
        sessionsTable.update(session_object["id"], session_object)
    return session_object["articles"][:count]


def filter_articles_by_feature(articles_df: pd.DataFrame, filter_feature: str, filter_list: list):
    if filter_feature is None or filter_list is None:
        return articles_df

    def any_wrapper(row, filterFeature, filterList):
        def list_to_lower_case(array: list): return [word.lower() for word in array]

        return any(freqWord in list_to_lower_case(row[filterFeature]) for freqWord in list_to_lower_case(filterList))

    return articles_df[articles_df.apply(any_wrapper, axis=1, args=(filter_feature, filter_list))]


def articles_to_json(articles_df: pd.DataFrame):
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


def get_categories(articles_df: pd.DataFrame):
    return list(set((articles_df['categories'])))


def collection_to_json(private_collection_object: pd.DataFrame):
    return private_collection_object.to_dict('collection_name')


def extract_articles_from_session_db(sessions_table_object: SessionObject, article_list: list):
    articles = sessions_table_object.articles
    return articles[articles['id'].isin(article_list)]