import uuid
import pandas as pd

class QueryObject(object):

    def __init__(self, query: str, articles_df: pd.DataFrame, offset: int):
        self.query = query
        self.articles = articles_df.to_dict('records')
        self.id = str(uuid.uuid4())
        self.offset = offset


class PrivateCollectionObject(object):

    def __init__(self, id: int, name: str, articleList: list):
        self.id = id
        self.name = name
        self.articleList = articleList
