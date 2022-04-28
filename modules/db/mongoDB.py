import pandas as pd
import pymongo
from urllib.parse import quote_plus
import uuid


class QueryObject:

    def __init__(self, query: str, articlesDF: pd.DataFrame, offset: int):
        self.query = query
        self.articles = articlesDF.to_dict('records')
        self.id = str(uuid.uuid4())
        self.offset = offset

class PrivateCollection:

    def __init__(self):
        pass


class MongoDB:

    __password = quote_plus("intel123")
    __client = pymongo.MongoClient(
        f"mongodb+srv://Intellimass:{__password}@intellimass.p8q7u.mongodb.net/sessions?retryWrites=true&w=majority")
    __db = __client["sessions"]
    __sessionsDB = __db["sessions"]

    @classmethod
    def insert(cls, dictToPush: QueryObject):
        cls.__sessionsDB.insert_one(dictToPush.__dict__)


    @staticmethod
    def update():
        pass

    @classmethod
    def get(cls, queryId):
        return cls.__sessionsDB.find_one({"id": queryId})






db = MongoDB()


