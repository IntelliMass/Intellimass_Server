import pandas as pd
import threading
from modules.searchQuery.searchInSemanticScholar import parallelSearch, appendMostFrequentFromAbstract


def extendArticlesList(dbObject: dict):

    dfOfArticles = pd.DataFrame(dbObject['articles'])
    offset = dbObject['size']
    query = dbObject['query']

    queryResults = []
    t1 = threading.Thread(target=parallelSearch, args=(query, offset, queryResults))
    t2 = threading.Thread(target=parallelSearch, args=(query, offset+100, queryResults))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    articlesDF = pd.DataFrame(queryResults)
    articlesDF.dropna(subset=["abstract"], inplace=True)
    articlesDF = articlesDF.apply(appendMostFrequentFromAbstract, args=(query,), axis=1)

    dfOfArticles.append(articlesDF, ignore_index=True)
    size = offset + 200

    return dfOfArticles, size
