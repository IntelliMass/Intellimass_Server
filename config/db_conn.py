import pymongo
from urllib.parse import quote_plus

password = quote_plus("intel123")

__client = pymongo.MongoClient(f"mongodb+srv://Intellimass:{password}@intellimass.p8q7u.mongodb.net/sessions?retryWrites=true&w=majority")
db = __client["sessions"]
sessionsDB = db["sessions"]
