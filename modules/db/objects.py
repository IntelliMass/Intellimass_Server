import uuid
import pandas as pd
import datetime


class SessionObject(object):
    def __init__(self, query: str, articles_df: pd.DataFrame = None, offset: int = None, id=None, breadcrumbs=None):
        self.query = query
        print(type(articles_df) == list)
        if type(articles_df) == list:
            self.articles = articles_df
        else:
            self.articles = articles_df.to_dict('records') if articles_df is not None else None
        self.id = id if id is not None else str(uuid.uuid4())
        self.offset = offset
        self.breadcrumbs = breadcrumbs if breadcrumbs else []


class PrivateCollectionObject(object):
    def __init__(self, user_id: str, collection_name: str):
        self.user_id = user_id
        self.collection_name = collection_name
        self.articles_list = []
