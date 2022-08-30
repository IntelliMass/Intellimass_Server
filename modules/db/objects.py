import uuid
import pandas as pd


class SessionObject(object):
    """
    Object that stored all User's session data
    """
    def __init__(self, query: str, operator: str, articles_df: pd.DataFrame = None, offset: int = None, id=None, breadcrumbs=None, iteration=0,
                 iteration_cache=None):
        if iteration_cache is None:
            iteration_cache = []
        self.query = query
        self.id = id if id is not None else str(uuid.uuid4())
        articles_df = pd.DataFrame(articles_df) if type(articles_df) != pd.DataFrame else articles_df
        articles_df['queryId'] = [self.id] * len(articles_df)
        self.articles = articles_df.to_dict('records')
        self.offset = offset
        self.breadcrumbs = breadcrumbs if breadcrumbs is not None else []
        self.operator = operator
        self.iteration = iteration
        self.iteration_cache = iteration_cache


class PrivateCollectionObject(object):
    """
    Object that stored user's private collection
    """
    def __init__(self, user_id: str, collection_name: str):
        self.user_id = user_id
        self.collection_name = collection_name
        self.articles_list = []
