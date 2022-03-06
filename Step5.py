import requests
import pandas as pd


def sendResponse(dfOfArticles: pd.DataFrame, connections, mostCommonTopics):

    response = {
        "articles": dfOfArticles.to_dict("records"),
        "network": connections,
        "most_common_topics": mostCommonTopics,
        "most_common_authors":
    }