import pymongo
from urllib.parse import quote_plus


class MongoDB:
    __password = quote_plus("intel123")
    __db = None

    def __init__(self, db_name):
        __client = pymongo.MongoClient(
            f"mongodb+srv://Intellimass:{self.__password}@intellimass.p8q7u.mongodb.net/{db_name}?retryWrites=true&w=majority")
        self.__db = __client[f"{db_name}"][f"{db_name}"]

    def insert(self, object_to_push: object):
        self.__db.insert_one(object_to_push.__dict__)

    def get(self, id_to_get: str, id_var="id"):
        objects = list(self.__db.find({id_var: id_to_get}))
        if len(objects) == 1:
            return objects[0]
        return objects

    def update(self, id_to_update: str, object_to_update: object, id_var="id"):
        update_filter = {id_var: id_to_update}
        set_params = {"$set": object_to_update.__dict__}
        self.__db.update_one(update_filter, set_params)

    def delete(self, id_to_delete: str, id_var="id"):
        delete_filter = {id_var: id_to_delete}
        self.__db.delete_one(delete_filter)

    def get_article(self, query_id: str, article_id: str):
        obj = list(self.__db.find_one({'id': query_id, 'article_id': article_id}))
        return obj


class SessionDB(MongoDB):
    def __init__(self):
        super().__init__("sessions")


class PrivateCollectionsDB(MongoDB):
    def __init__(self):
        super().__init__("private_Collections")

    def is_collection_exists(self, id_to_get: str, collection_name: str):
        objects = list(self.__db.find({'user_id': id_to_get, 'collection_name': collection_name}))
        if objects:
            return True
        else:
            return False


sessionsTable = SessionDB()
privateCollectionsTable = PrivateCollectionsDB()
