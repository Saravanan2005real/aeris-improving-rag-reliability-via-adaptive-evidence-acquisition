import os
import json
import pytest
from app.performance_cache import AERISCache

def create_cache_file(filepath, namespace, key, value):
    c = AERISCache(filepath)
    c.set(namespace, key, value)
    return filepath

def test_1_existing_cache_loads_correctly(tmp_path):
    path_a = str(tmp_path / "cache_A.json")
    create_cache_file(path_a, "ns1", "key1", "valueA")
    
    cache = AERISCache(path_a)
    assert cache.get("ns1", "key1") == "valueA"

def test_2_missing_cache_starts_empty(tmp_path):
    path_a = str(tmp_path / "cache_A.json")
    create_cache_file(path_a, "ns1", "key1", "valueA")
    cache_a = AERISCache(path_a)
    
    # Load missing cache B in same process
    path_b = str(tmp_path / "cache_B.json")
    cache_b = AERISCache(path_b)
    
    assert cache_b.get("ns1", "key1") is None
    assert cache_b._cache == {}

def test_3_sequential_cache_switching(tmp_path):
    path_a = str(tmp_path / "cache_A.json")
    path_b = str(tmp_path / "cache_B.json")
    path_c = str(tmp_path / "cache_C.json")
    
    create_cache_file(path_a, "ns1", "key1", "valA")
    create_cache_file(path_b, "ns1", "key1", "valB")
    create_cache_file(path_c, "ns1", "key1", "valC")
    
    cache = AERISCache(path_a)
    assert cache.get("ns1", "key1") == "valA"
    
    cache.cache_file = path_b
    cache._load()
    assert cache.get("ns1", "key1") == "valB"
    
    cache.cache_file = path_c
    cache._load()
    assert cache.get("ns1", "key1") == "valC"

def test_4_existing_b_after_a(tmp_path):
    path_a = str(tmp_path / "cache_A.json")
    path_b = str(tmp_path / "cache_B.json")
    
    create_cache_file(path_a, "ns1", "key", "valA")
    create_cache_file(path_b, "ns2", "key", "valB")
    
    cache = AERISCache(path_a)
    assert cache.get("ns1", "key") == "valA"
    
    cache.cache_file = path_b
    cache._load()
    assert cache.get("ns2", "key") == "valB"
    assert cache.get("ns1", "key") is None

def test_5_corrupt_cache_isolation(tmp_path):
    path_a = str(tmp_path / "cache_A.json")
    path_b = str(tmp_path / "cache_B.json")
    
    create_cache_file(path_a, "ns1", "key", "valA")
    
    with open(path_b, "w") as f:
        f.write("{invalid json")
        
    cache = AERISCache(path_a)
    assert cache.get("ns1", "key") == "valA"
    
    cache.cache_file = path_b
    cache._load()
    
    assert cache._cache == {}
    assert cache.get("ns1", "key") is None

def test_6_variant_style_isolation(tmp_path):
    path_full = str(tmp_path / "test_cache_FULL_AERIS.json")
    path_no_adapt = str(tmp_path / "test_cache_NO_ADAPTIVE_RETRIEVAL.json")
    path_no_query = str(tmp_path / "test_cache_NO_QUERY_REFORMULATION.json")
    
    create_cache_file(path_full, "ns", "key", "val_full")
    create_cache_file(path_no_adapt, "ns", "key", "val_no_adapt")
    create_cache_file(path_no_query, "ns", "key", "val_no_query")
    
    cache = AERISCache(path_full)
    assert cache.get("ns", "key") == "val_full"
    
    cache.cache_file = path_no_adapt
    cache._load()
    assert cache.get("ns", "key") == "val_no_adapt"
    
    cache.cache_file = path_no_query
    cache._load()
    assert cache.get("ns", "key") == "val_no_query"
    
def test_7_regression_original_failure(tmp_path):
    # This precisely simulates the Step 22C cache failure.
    path_full = str(tmp_path / "test_cache_FULL_AERIS_regression.json")
    path_missing = str(tmp_path / "test_cache_NO_ADAPTIVE_RETRIEVAL_missing.json")
    
    create_cache_file(path_full, "ns", "key", "full_aeris_value")
    
    cache = AERISCache(path_full)
    assert cache.get("ns", "key") == "full_aeris_value"
    
    cache.cache_file = path_missing
    cache._load()
    
    # If the bug were present, this would be "full_aeris_value"
    assert cache.get("ns", "key") is None
    assert cache._cache == {}

if __name__ == "__main__":
    pytest.main(["-v", __file__])
