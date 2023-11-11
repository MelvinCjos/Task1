
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client.task_db  
profile_picture_collection = db.profile_pic
