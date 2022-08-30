import pymongo
from urllib.parse import quote_plus
from multiprocessing import Lock
import datetime

lock = Lock()

class MongoDB:
    __password = quote_plus("intel123")
    __db = None

    def __init__(self, db_name):
        __client = pymongo.MongoClient(
            f"mongodb+srv://Intellimass:{self.__password}@intellimass.p8q7u.mongodb.net/{db_name}?retryWrites=true&w=majority")
        self.db = __client[f"{db_name}"][f"{db_name}"]

    def insert(self, object_to_push: object):
        self.db.insert_one(object_to_push.__dict__)

    def get(self, id_to_get: str, id_var="id"):
        objects = list(self.__db.find({id_var: id_to_get}))
        for object in objects:
            del object['_id']
        if len(objects) == 1:
            return objects[0]
        return objects

    def update(self, id_to_update: str, object_to_update: object, id_var="id"):
        if type(object_to_update) is type(object):
            object_to_update = object_to_update.__dict__
        if '_id' in object_to_update.keys():
            print(object_to_update['_id'])
            del object_to_update['_id']
        update_filter = {id_var: id_to_update}
        set_params = {"$set": object_to_update}
        lock.acquire()
        self.db.update_one(update_filter, set_params)
        lock.release()

    def delete(self, id_to_delete: str, id_var="id"):
        delete_filter = {id_var: id_to_delete}
        self.db.delete_one(delete_filter)

    def update_paper(self, id_to_update: str, collection_name: str, object_to_update: str):
        update_filter = {'user_id': id_to_update, "collection_name": collection_name} 
        set_params = {'articles_list': object_to_update}      
        self.db.update_one(update_filter, {'$push': set_params})

    def pop_paper(self, id_to_pop: str, collection_name: str, object_to_pop: str):
        update_filter = {'user_id': id_to_pop, "collection_name": collection_name}
        # set_params = {'articles_list': object_to_pop}
        set_params = {'articles_list': {'paperId': object_to_pop}}
        self.db.update_one(update_filter, {'$pull': set_params})


class SessionDB(MongoDB):
    def __init__(self):
        super().__init__("sessions")

    def get_article_paperid(self, query_id: str, article_id: str):
        def find_article_in_articles(obj, arc_id):
            for article in obj["articles"]:
                if article["paperId"] == arc_id:
                    return article
            return None

        def append_fields(all_articles, f_article):
            if 'query' not in f_article.keys():
                f_article['query'] = all_articles['query']
            if 'timestamp' not in f_article.keys():
                f_article['timestamp'] = datetime.datetime.now().strftime("%d/%m/%Y | %H:%M:%S")
            return f_article

        get_filter = {'id': query_id, 'articles': {'$elemMatch': {'paperId': article_id}}}
        found_obj = self._MongoDB__db.find_one(get_filter)
        if found_obj is not None:
            found_article = find_article_in_articles(found_obj, article_id)
            if found_article is not None:
                if '_id' in found_article.keys():
                    del found_article['_id']
                found_article = append_fields(found_obj, found_article)
                return found_article
        return None


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
        self._MongoDB__db.delete_one(delete_filter)


sessionsTable = SessionDB()
privateCollectionsTable = PrivateCollectionsDB()
