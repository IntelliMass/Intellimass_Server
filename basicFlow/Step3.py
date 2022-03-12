import pandas as pd


def getConnectionsByFeature(dfOfArticles: pd.DataFrame, feature: str):

    connections = []

    # Handle feature='Authors'
    if feature == 'Authors':
        for _, article1 in dfOfArticles.iterrows():
            articleConnections = []
            article1AuthorIds = [article2['authorId'] for article2 in article1['authors']]
            for _, article2 in dfOfArticles.iterrows():
                article2AuthorIds = [article2['authorId'] for article2 in article2['authors']]
                authorInBothArticles = any(author in article1AuthorIds for author in article2AuthorIds)
                if authorInBothArticles and article1['paperId'] != article2['paperId']:
                    articleConnections.append(1)
                else:
                    articleConnections.append(0)
            connections.append(articleConnections)
        return connections
