from Step1 import searchQuerySemanticScholar
from Step2 import extendArticles
from Step3 import getConnectionsByFeature
from Step4 import getMostCommons
from Step5 import arrangeResponse
import time


def handleQuery(query, numOfResults):

    start = time.time()
    ########################################################################
    # Step 1 - Search in Semantic Scholar
    dfOfArticles = searchQuerySemanticScholar(query, numOfResults)
    print(f"STEP 1 Time: {time.time()-start}")
    ########################################################################
    # Step 2 - Extend with topics
    dfOfArticles = extendArticles(dfOfArticles, numOfResults)
    print(f"STEP 2 Time: {time.time() - start}")
    ########################################################################
    # Step 3 - Set Connections
    feature = "Authors"
    connections = getConnectionsByFeature(dfOfArticles, feature)
    print(f"STEP 3 Time: {time.time() - start}")
    ########################################################################
    # Step 4 - Get Array of most common topics
    mostCommonTopics, mostCommonAuthors = getMostCommons(dfOfArticles)
    print(f"STEP 4 Time: {time.time() - start}")
    print(mostCommonTopics)
    print(len(mostCommonTopics))
    print(mostCommonAuthors)
    print(len(mostCommonAuthors))
    print(len(dfOfArticles))
    ########################################################################
    # Step 5 - Arrange all together and send response
    res = arrangeResponse(dfOfArticles, connections, mostCommonTopics, mostCommonAuthors)
    return res
    ########################################################################


# handleQuery("IOT", 200)