import pymongo
from urllib.parse import quote_plus


class MongoDB:
    __password = quote_plus("intel123")
    __db = None

    def __init__(self, db_name):
        __client = pymongo.MongoClient(
            f"mongodb+srv://Intellimass:{self.__password}@intellimass.p8q7u.mongodb.net/{db_name}?retryWrites=true&w=majority")
        self.__db = __client[f"{db_name}"][f"{db_name}"]

    @classmethod
    def insert(cls, object_to_push: object):
        cls.__db.insert_one(object_to_push.__dict__)

    @classmethod
    def get(cls, id_to_get: str):
        return cls.__db.find_one({"id": id_to_get})

    @classmethod
    def update(cls, id_to_update: str, object_to_update: object):
        update_filter = {'id': id_to_update}
        set_params = {"$set": object_to_update.__dict__}
        cls.__db.update_one(update_filter, set_params)

    @classmethod
    def delete(cls, id_to_delete):
        delete_filter = {'id': id_to_delete}
        cls.__db.delete_one(delete_filter)


class SessionDB(MongoDB):
    def __init__(self):
        super().__init__("sessions")


class PrivateCollectionsDB(MongoDB):
    def __init__(self):
        super().__init__("private_Collections")


sessionsTable = SessionDB()
privateCollectionsTable = PrivateCollectionsDB()
