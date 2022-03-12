import pandas as pd
from collections import Counter
from config import MAX_COMMON_FEATURE

def getMostCommons(dfOfArticles: pd.DataFrame):
    topicsCounter = []
    authorsCounter = []
    for _, article in dfOfArticles.iterrows():
        topicsCounter.extend([topicName['topic'] for topicName in article['topics']])
        authorsCounter.extend([author['name'] for author in article['authors']])
    mostCommonTopics = dict(Counter(topicsCounter))
    mostCommonTopics = {k: v for k, v in sorted(mostCommonTopics.items(), key=lambda item: item[1], reverse=True)[:MAX_COMMON_FEATURE]}
    mostCommonAuthors = dict(Counter(authorsCounter))
    mostCommonAuthors = {k: v for k, v in sorted(mostCommonAuthors.items(), key=lambda item: item[1], reverse=True)[:MAX_COMMON_FEATURE]}
    return mostCommonTopics, mostCommonAuthors
