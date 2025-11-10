import os
import time
from os import getenv
from pymongo.errors import ServerSelectionTimeoutError # Import the specific error

try:
    from pymongo import MongoClient
except Exception:
    MongoClient = None
    ServerSelectionTimeoutError = Exception 

MONGO_URI = getenv("MONGO_DB_URI") or None

class DBClient:
    def __init__(self, uri=None):
        self.uri = uri or MONGO_URI
        self.enabled = False
        self._cache = {}    # fallback in-memory: video_id -> record
        self._query_map = {}  # query -> video_id
        
        if self.uri and MongoClient:
            try:
                # Set a low timeout for quick connection check
                self.client = MongoClient(self.uri, serverSelectionTimeoutMS=5000) 
                
                # PING the server to check connectivity explicitly
                self.client.admin.command('ping')
                
                # 💡 FIX: Database name is explicitly "AbhiMusic" based on your URI
                self.db = self.client["AbhiMusic"]

                self.videos = self.db["videos"]
                self.query_map = self.db["query_map"]
                
                # ensure indexes
                self.videos.create_index("video_id", unique=True)
                self.query_map.create_index("query", unique=True)
                self.enabled = True
                print("[DB] MongoDB connected successfully.")
                
            except ServerSelectionTimeoutError as e:
                print(f"[DB] MongoDB connect failed (Timeout/Network): {e}")
                self.enabled = False
            except Exception as e:
                # Catching generic error after ping failure
                print(f"[DB] MongoDB connect failed (Other error): {e}")
                self.enabled = False
        else:
            if not MongoClient and self.uri:
                print("[DB] pymongo not installed — using in-memory fallback.")
            self.enabled = False

    def save_video(self, video_id, obj):
        obj["video_id"] = video_id
        obj["updated_at"] = int(time.time())
        if self.enabled:
            try:
                self.videos.update_one({"video_id": video_id}, {"$set": obj}, upsert=True)
                return True
            except Exception as e:
                print("[DB] save_video error:", e)
                self._cache[video_id] = obj
                return False
        else:
            self._cache[video_id] = obj
            return True

    def get_by_video_id(self, video_id):
        if self.enabled:
            try:
                doc = self.videos.find_one({"video_id": video_id})
                if doc:
                    doc.pop("_id", None)
                return doc
            except Exception as e:
                print("[DB] get_by_video_id error:", e)
                return self._cache.get(video_id)
        else:
            return self._cache.get(video_id)

    def save_query_map(self, query, video_id):
        q = query.strip().lower()
        if self.enabled:
            try:
                self.query_map.update_one({"query": q}, {"$set": {"query": q, "video_id": video_id}}, upsert=True)
                return True
            except Exception as e:
                print("[DB] save_query_map error:", e)
                self._query_map[q] = video_id
                return False
        else:
            self._query_map[q] = video_id
            return True

    def get_video(self, query_or_videoid):
        """
        Try to return a saved record by video_id or by query string.
        """
        q = str(query_or_videoid).strip().lower()
        # if it looks like video_id (11 chars typical) check direct
        if len(q) in (11, 10, 12):  # rough guess
            rec = self.get_by_video_id(q)
            if rec:
                return rec
        # else check query_map
        if self.enabled:
            try:
                r = self.query_map.find_one({"query": q})
                if r and r.get("video_id"):
                    return self.get_by_video_id(r["video_id"])
            except Exception as e:
                print("[DB] get_video error:", e)
        else:
            vid = self._query_map.get(q)
            if vid:
                return self._cache.get(vid)
        return None
