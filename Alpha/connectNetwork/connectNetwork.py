import pandas as pd
import json
import boto3


def getConnectionsByFeature(articles: list, feature='default'):
    dfOfArticles = pd.DataFrame(articles)
    connections = []

    # Handle feature='Authors'
    if feature.lower() == 'authors':
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


def lambda_handler(event, context):

    s3 = boto3.client('s3')
    key = event['Records'][0]['s3']['object']['key']

    object = s3.get_object(Bucket='intellimass-sessions', Key=key)
    sessionData = json.loads(object['Body'].read())
    ID = sessionData['Id']

    articles = sessionData['articles']
    if 'feature' in sessionData.keys():
        feature = sessionData['feature']
    else:
        feature = 'default'
    connections = getConnectionsByFeature(articles, feature)

    sessionData['connections'] = connections

    s3.put_object(
        Body=json.dumps(connections).encode('UTF-8'),
        Bucket="intellimass-sessions",
        Key=f"Networks/{ID}_{feature}"
    )
