import uuid
import pandas as pd


class SessionObject(object):

    def __init__(self, query: str, articles_df: pd.DataFrame, offset: int, id=None):
        self.query = query
        self.articles = articles_df.to_dict('records')
        self.id = id if id is not None else str(uuid.uuid4())
        self.offset = offset


class PrivateCollectionObject(object):

    def __init__(self, user_id: str, collection_name: str, article_list: list, query_id: str):
        self.user_id = user_id
        self.collection_name = collection_name
        self.article_list = article_list
        self.query_id = query_id


class TTTTOOOOOCCHANGEEEEEPrivateCollectionObject(object):

    def __init__(self, user_id: str, collection_name: str, article_list: list, query_id: str):
        self.user_id = user_id
        self.collections = {}
        self.article_list = article_list
        self.query_id = query_id
