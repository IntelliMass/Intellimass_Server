import pandas as pd
from collections import Counter
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
import string


def append(articles_df: pd.DataFrame, query: str):
    """
    Appends frequent words column to articles DataFrame
    :param articlesDF: :type: pd.DateFrame
    :param query: :type: str (query to ignore)
    :return: articlesDF with frequent words column
    """
    def appendMostFrequentFromAbstract(articleData, query):
        """
        :param articleData:  article Object (Row in the DataFrame)
        :param query: User's query to ignore
        :return: Frequencies of words in abstract
        """
        abstract = articleData['abstract']
        MY_STOP = ['article', 'based']
        for q in query:
            q_splitted = q.split()
            for q in q_splitted:
                MY_STOP.extend([q.lower(), q.lower() + 's', q.lower() + "'s"])
        for sign in string.punctuation:
            abstract = abstract.replace(sign, '')

        splited = [word for word in abstract.split() if
                   word.lower() not in ENGLISH_STOP_WORDS and word.lower() not in MY_STOP]
        counter = Counter(splited)
        most_occur = counter.most_common(5)
        articleData['frequentWords'] = [freqWord[0] for freqWord in most_occur]
        return articleData
    return articles_df.apply(appendMostFrequentFromAbstract, args=(query,), axis=1)
