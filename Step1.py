import requests
import time
import json
import pandas as pd
import math


def searchQuerySemanticScholar(query: str, numOfResults=50):
    query = query.replace(' ', '+')
    queryResults = []
    numOfResultsWithInsurance = math.floor(numOfResults * 1.2)
    for num in range(0, numOfResultsWithInsurance, 100):
        header = {"x-api-key": "qZWKkOKyzP5g9fgjyMmBt1MN2NTC6aT61UklAiyw"}
        url = f"http://api.semanticscholar.org/graph/v1/paper/search?query={query}&offset={num}&limit={100}&fields=title,authors,isOpenAccess,fieldsOfStudy,year,abstract"
        res = requests.get(url, headers=header)

        # Handling fail responses
        # ->
        #########################

        dictRes = json.loads(res.text)
        resData = dictRes['data']
        queryResults.extend(resData)

    # print(f"Time: {time.time() - start} secs")
    response = pd.DataFrame(queryResults)
    return response
