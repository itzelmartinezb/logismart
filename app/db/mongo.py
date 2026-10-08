from contextlib import contextmanager
from datetime import datetime
from pymongo import MongoClient, ASCENDING
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError

class MongoDB:
    def __init__(self, uri: str, database: str):
        self.uri, self.database_name = uri, database
        self.client = None
        self.db = None

    def connect(self):
        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=4000)
            self.client.admin.command("ping")
            self.db = self.client[self.database_name]
            self._indexes()
            return True, "MongoDB conectado correctamente"
        except ServerSelectionTimeoutError as e:
            self.client = self.db = None
            return False, f"No se pudo conectar con MongoDB: {e}"
        except PyMongoError as e:
            self.client = self.db = None
            return False, f"Error de MongoDB: {e}"

    def _indexes(self):
        for collection, fields in {
            "camiones": [("placa", ASCENDING)],
            "accesos": [("marca_tiempo", ASCENDING)],
            "incidentes": [("fecha", ASCENDING), ("estado", ASCENDING)],
            "riesgos_eticos": [("categoria", ASCENDING)],
            "evaluaciones_llm": [("fecha", ASCENDING)],
        }.items():
            self.db[collection].create_index(fields)

    def close(self):
        if self.client: self.client.close()

    def collection(self, name):
        if self.db is None: raise ConnectionError("MongoDB no está conectado")
        return self.db[name]

    def create(self, collection, data):
        data = dict(data); data.setdefault("fecha", datetime.now())
        return self.collection(collection).insert_one(data).inserted_id

    def find(self, collection, filters=None, limit=200):
        return list(self.collection(collection).find(filters or {}).sort("_id", -1).limit(limit))

    def get(self, collection, doc_id):
        from bson import ObjectId
        return self.collection(collection).find_one({"_id": ObjectId(doc_id)})

    def update(self, collection, doc_id, data):
        from bson import ObjectId
        return self.collection(collection).update_one({"_id": ObjectId(doc_id)}, {"$set": data})

    def delete(self, collection, doc_id):
        from bson import ObjectId
        return self.collection(collection).delete_one({"_id": ObjectId(doc_id)})

    def access_by_plate(self, placa):
        return list(self.collection("accesos").find({"placa": placa}).sort("marca_tiempo", -1).limit(20))

    def incident_week_aggregation(self):
        return list(self.collection("incidentes").aggregate([
            {"$group": {"_id": {"categoria": "$clasificacion.categoria", "semana": {"$dateToString": {"format": "%G-W%V", "date": "$fecha"}}}, "total": {"$sum": 1}}},
            {"$sort": {"_id.semana": 1, "_id.categoria": 1}}
        ]))
