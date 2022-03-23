import pandas as pd


def list_to_lower_case(array: list):
    return [word.lower() for word in array]


def any_wrapper(row, filterFeature, filterList):
    # return False if (set((row[filterFeature])).intersection(set(filterList)) == set()) else True
    return any(freqWord in list_to_lower_case(row[filterFeature]) for freqWord in list_to_lower_case(filterList))


def filerArticlesByKeywords(listOfArticles: list, filterList: list, filterFeature: str):

    print(f"filterFeature: {filterFeature}")
    print(f"filterList: {filterList}")
    dfOfArticles = pd.DataFrame(listOfArticles)
    # if filterFeature == "frequentWords":
    #     dfOfArticles = dfOfArticles[dfOfArticles.apply(any, args=((freqWord2 in listOfArticles[filterFeature] for freqWord2 in filterList),))]
    dfOfArticles = dfOfArticles[dfOfArticles.apply(any_wrapper, axis=1, args=(filterFeature, filterList))]
    for _, row in dfOfArticles.iterrows():
        print(row[filterFeature])
    print(f"num of articles: {len(dfOfArticles)}")
    return dfOfArticles.to_dict('records')
