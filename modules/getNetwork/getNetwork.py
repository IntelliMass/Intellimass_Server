import itertools
import pandas as pd


def connectByDEFAULT(dfOfArticles: pd.DataFrame):
    pass


def connectByTopics(dfOfArticles: pd.DataFrame):

    links = []
    for _, article1 in dfOfArticles.iterrows():
        topics1 = [topic['topic'] for topic in article1['topics']]
        for _, article2 in dfOfArticles.iterrows():
            topics2 = [topic['topic'] for topic in article2['topics']]
            if any(topic in topics1 for topic in topics2):
                tmpForLink = []
                for topic in topics1:
                    if topic in topics2:
                        tmpForLink.append(topic)
                if len(tmpForLink) > 2:
                    links.append(
                        {
                            "source": article1['paperId'],
                            "target": article2['paperId'],
                            "value": tmpForLink
                        }
                    )
    return links


def connectByFrequentwords(dfOfArticles: pd.DataFrame):

    links = []
    for _, article1 in dfOfArticles.iterrows():
        freqs1 = article1['frequentWords']
        for _, article2 in dfOfArticles.iterrows():
            freqs2 = article2['frequentWords']
            if any(word in freqs1 for word in freqs2):
                tmpForLink = []
                for word in freqs1:
                    if word in freqs2:
                        tmpForLink.append(word)
                links.append(
                    {
                        "source": article1['paperId'],
                        "target": article2['paperId'],
                        "value": tmpForLink
                    }
                )
    return links


def connectByAuthors(dfOfArticles: pd.DataFrame):
    links = []
    for i, article1 in dfOfArticles.iterrows():
        article1AuthorIds = [author['authorId'] for author in article1['authors']]
        for _, article2 in itertools.islice(dfOfArticles.iterrows(), i + 1, None):
            if article1['paperId'] == article2['paperId']:
                continue
            article2AuthorIds = [author['authorId'] for author in article2['authors']]
            commonAuthorsInBothArticles = list(set(article1AuthorIds).intersection(article2AuthorIds))
            commonAuthorsInBothArticles = [author['name'] for author in article1['authors'] if
                                           author['authorId'] in commonAuthorsInBothArticles]
            if len(commonAuthorsInBothArticles) > 0:
                links.append(
                    {
                        "source": article1['paperId'],
                        "target": article2['paperId'],
                        "value": commonAuthorsInBothArticles
                    }
                )
    return links


def getNetwork(listOfArticles: list, feature: str):
    """

        :param articles:
        :param feature:
        :return: links: [
                            {
                                source: str,    e.g     "e6e1989b2df588a6ece0e4dd520f34b20ac5cf14"
                                target: str,    e.g     "893644d781fcbcad807f97a8494c14f66c0684e5
                                size:   int,    e.g
                                color:  str,    e.g
                                value:  list     e.g     ['Behnam Zakeri']
                            }
                        ]
        :type: links : list


        """

    dfOfArticles = pd.DataFrame(listOfArticles)
    feature = feature.lower().replace(' ', '').capitalize()
    return eval(f"connectBy{feature}(dfOfArticles)")
