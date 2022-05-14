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

    def update_paper(self, id_to_update: str, collection_name: str, object_to_update: str):
        update_filter = {'user_id': id_to_update, "collection_name": collection_name} 
        set_params = {'articles_list': object_to_update}      
        self.__db.update_one(update_filter, {'$push': set_params})

    def pop_paper(self, id_to_pop: str, collection_name: str, object_to_pop: str):
        update_filter = {'user_id': id_to_pop, "collection_name": collection_name}
        set_params = {'articles_list': object_to_pop}      
        self.__db.update_one(update_filter, {'$pull': set_params})


class SessionDB(MongoDB):
    def __init__(self):
        super().__init__("sessions")

    def get_article_paperid(self, query_id: str, article_id: str):
        get_filter = {'id': query_id, 'articles': {'$elemMatch': {'paperId': article_id}}}
        found_obj = self._MongoDB__db.find_one({}, get_filter)
        print(f'found_obj: {found_obj}')
        del found_obj['_id']
        return found_obj

    # temp1 = {'_id': 'blabla', 'articles': [{'paperId': 'blalba', 'title': '...'}]}


class PrivateCollectionsDB(MongoDB):
    def __init__(self):
        super().__init__("private_Collections")

    def is_collection_exists(self, id_to_get: str, collection_name: str):
        objects = list(self._MongoDB__db.find({'user_id': id_to_get, 'collection_name': collection_name}))
        if objects:
            return True
        else:
            return False

    def replace(self, id_to_get: str, field_to_find: str, field_to_replace: str):
        myquery = {"user_id": id_to_get, "collection_name": field_to_find}
        new_values = {"$set": {"collection_name": field_to_replace}}
        self._MongoDB__db.update_one(myquery, new_values)

    def delete_collection(self, id_to_delete: str, collection_name: str):
        delete_filter = {"user_id": id_to_delete, "collection_name": collection_name}
        result = self._MongoDB__db.delete_one(delete_filter)
        print(result)


sessionsTable = SessionDB()
privateCollectionsTable = PrivateCollectionsDB()
