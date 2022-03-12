import pandas as pd


def arrangeResponse(dfOfArticles: pd.DataFrame, connections, mostCommonTopics, mostCommonAuthors):

    response = {
        "articles": dfOfArticles.to_dict("records"),
        "network": connections,
        "most_common_topics": mostCommonTopics,
        "most_common_authors": mostCommonAuthors
    }

    return response
