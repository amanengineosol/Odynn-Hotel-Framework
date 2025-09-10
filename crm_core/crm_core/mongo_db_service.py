from pymongo import MongoClient
from datetime import datetime, timezone
import os
import urllib.parse

# Fetch MongoDB environment variables
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME')
username = os.getenv('MONGO_DB_USER')
password = os.getenv('MONGO_DB_PASSWORD')

# URL encode username and password for MongoDB URI
username_encoded = urllib.parse.quote_plus(str(username)) if username else ''
password_encoded = urllib.parse.quote_plus(str(password)) if password else ''

# Construct the MongoDB URI with authentication if username and password are provided
if username and password:
    MONGO_URI = f'mongodb://{username_encoded}:{password_encoded}@mongodb:27017/{MONGO_DB_NAME}?authSource=admin'
else:
    # Fallback to no authentication local URI
    MONGO_URI = f'mongodb://mongodb:27017/{MONGO_DB_NAME}'

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

