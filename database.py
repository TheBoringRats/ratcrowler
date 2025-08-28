from config import config
from pymongo import MongoClient

class Database:
    def __init__(self, db_name="webcrawler_db"):
        self.client = MongoClient(config.MONGODB_URI)
        self.db = self.client[db_name]

    def get_collection(self, collection_name):
        return self.db[collection_name]
    def insert_document(self, document, collection_name="webdata"):
        """Insert a document into the specified collection."""
        collection = self.get_collection(collection_name)

        # Handle both single documents and lists of documents
        if isinstance(document, list):
            if len(document) == 0:
                return []
            result = collection.insert_many(document)
            return result.inserted_ids
        else:
            result = collection.insert_one(document)
            return result.inserted_id

    def close(self):
        self.client.close()
