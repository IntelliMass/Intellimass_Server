import uuid
import pandas as pd


class SessionObject(object):

    def __init__(self, query: str, articles_df: pd.DataFrame, offset: int):
        self.query = query
        self.articles = articles_df.to_dict('records')
        self.id = str(uuid.uuid4())
        self.offset = offset


class PrivateCollectionObject(object):

    def __init__(self, user_id: str, collection_name: str, article_list: list):
        self.user_id = user_id
        self.collection_name = collection_name
        self.article_list = article_list
