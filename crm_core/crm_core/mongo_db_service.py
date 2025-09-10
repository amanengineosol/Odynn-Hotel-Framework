from pymongo import MongoClient
from datetime import datetime, timezone
import os



MONGO_DB_NAME = os.getenv('MONGO_DB_NAME')

MONGO_URI = os.getenv('MONGO_URI')
if not MONGO_URI:
    raise ValueError("MONGO_URI is not available")


# Create MongoClient
client = MongoClient(MONGO_URI)

# Access database and collections
db = client[MONGO_DB_NAME]
response_collection = db['response_out']
request_collection = db['request_in']

def save_request_response_to_db(request_data: dict, response_data: dict):
    document = {
        'request': request_data,
        'response': response_data,
        'timestamp': datetime.now(timezone.utc)
    }
    response_collection.insert_one(document)

def save_request(request_data: dict):
    document = {
        'request': request_data,
        'timestamp': datetime.now(timezone.utc)
    }
    request_collection.insert_one(document)

