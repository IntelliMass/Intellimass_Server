import pandas as pd
from collections import Counter

MAX_COMMON_FEATURE = 20


def getMetadata(listOfArticles: list):

    dfOfArticles = pd.DataFrame(listOfArticles)

    topicsCounter = []
    frequentWordsCounter = []

    for _, article in dfOfArticles.iterrows():
        # topicsCounter.extend([topicName['topic'] for topicName in article['topics']])
        frequentWordsCounter.extend([frequentWord for frequentWord in article['frequentWords']])

    # mostCommonTopics = dict(Counter(topicsCounter))
    # mostCommonTopics = [{"title": k.capitalize(), "rank": v} for k, v in
    #                     sorted(mostCommonTopics.items(), key=lambda item: item[1], reverse=True)[:MAX_COMMON_FEATURE]]
    # print(frequentWordsCounter)
    # print(Counter(frequentWordsCounter))
    # print(dict(Counter(frequentWordsCounter)))
    mostCommonFrequentWords = dict(Counter(frequentWordsCounter))
    mostCommonFrequentWords = [{"title": k if k[0].isupper() else k.capitalize(), "rank": v} for k, v in
                sorted(mostCommonFrequentWords.items(), key=lambda item: item[1], reverse=True)[:MAX_COMMON_FEATURE]]

    # return mostCommonTopics, mostCommonFrequentWords
    # return mostCommonTopics
    return mostCommonFrequentWords


