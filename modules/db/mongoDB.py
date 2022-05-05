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
        objects = self.__db.find({id_var: id_to_get}).__dict__
        return objects

    def update(self, id_to_update: str, object_to_update: object, id_var="id"):
        update_filter = {id_var: id_to_update}
        set_params = {"$set": object_to_update.__dict__}
        self.__db.update_one(update_filter, set_params)

    def delete(self, id_to_delete: str, id_var="id"):
        delete_filter = {id_var: id_to_delete}
        self.__db.delete_one(delete_filter)


class SessionDB(MongoDB):
    def __init__(self):
        super().__init__("sessions")


class PrivateCollectionsDB(MongoDB):
    def __init__(self):
        super().__init__("private_Collections")


sessionsTable = SessionDB()
privateCollectionsTable = PrivateCollectionsDB()