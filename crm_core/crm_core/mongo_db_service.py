from pymongo import MongoClient
from datetime import datetime, timezone
import os

# Local MongoDB connection string for Docker container
MONGO_URI = os.getenv('MONGO_URI') 
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME')

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]

response_collection = db['request_response_history']
request_collection = db['requests']

def save_request_response(request_data: dict, response_data: dict):
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
