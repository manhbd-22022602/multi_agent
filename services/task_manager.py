from pymongo import MongoClient
# from configs.settings import MONGO_URI

MONGO_URI="sample"
client = MongoClient(MONGO_URI)
db = client["multiagent"]

def create_task(**kwargs):
    return db.tasks.insert_one(kwargs).inserted_id

def update_task(task_id, **kwargs):
    db.tasks.update_one({"_id": task_id}, {"$set": kwargs})

def get_tasks(project_id, **filters):
    return list(db.tasks.find({"project_id": project_id, **filters}))
