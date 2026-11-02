import json
import os
import hashlib
from typing import Any, Optional

class AERISCache:
    def __init__(self, cache_file="data/aeris_cache.json"):
        self.cache_file = cache_file
        self.enabled = os.environ.get("AERIS_CACHE_ENABLED", "true").lower() == "true"
        self._cache = {}
        self._load()
        
    def _load(self):
        self._cache = {}
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as f:
                    self._cache = json.load(f)
            except:
                self._cache = {}
                
    def _save(self):
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        with open(self.cache_file, "w") as f:
            json.dump(self._cache, f)
            
    def _hash(self, key_data: str) -> str:
        return hashlib.md5(key_data.encode("utf-8")).hexdigest()
        
    def get(self, namespace: str, key_data: Any) -> Optional[Any]:
        if not self.enabled: return None
        key_str = f"{namespace}:{json.dumps(key_data, sort_keys=True)}"
        h = self._hash(key_str)
        return self._cache.get(h)
        
    def set(self, namespace: str, key_data: Any, value: Any):
        if not self.enabled: return
        key_str = f"{namespace}:{json.dumps(key_data, sort_keys=True)}"
        h = self._hash(key_str)
        self._cache[h] = value
        self._save()

aeris_cache = AERISCache()
