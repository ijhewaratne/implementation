"""
Unit tests for Cache Manager.

Tests the caching system for simulation results.
"""

import pytest
import sys
from pathlib import Path
import geopandas as gpd
from shapely.geometry import Point
import tempfile
import shutil

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.orchestration import SimulationCache


@pytest.fixture
def temp_cache_dir():
    """Create temporary cache directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_buildings():
    """Create sample building dataset."""
    return gpd.GeoDataFrame({
        'GebaeudeID': ['B001', 'B002', 'B003'],
        'heating_load_kw': [50.0, 75.0, 30.0],
        'geometry': [Point(0, 0), Point(100, 0), Point(50, 100)]
    }, crs='EPSG:25833')


def test_cache_initialization(temp_cache_dir):
    """Test cache manager initializes correctly."""
    cache = SimulationCache(cache_dir=temp_cache_dir)
    
    assert cache.cache_dir.exists()
    assert (cache.cache_dir / "dh").exists()
    assert (cache.cache_dir / "hp").exists()


def test_cache_miss(temp_cache_dir, sample_buildings):
    """Test cache miss (no cached result)."""
    cache = SimulationCache(cache_dir=temp_cache_dir)
    
    params = {"supply_temp_c": 85, "return_temp_c": 55}
    result = cache.get("DH", sample_buildings, params)
    
    assert result is None
    assert cache.stats["misses"] == 1
    assert cache.stats["hits"] == 0


def test_cache_set_and_get(temp_cache_dir, sample_buildings):
    """Test caching a result and retrieving it."""
    cache = SimulationCache(cache_dir=temp_cache_dir)
    
    params = {"supply_temp_c": 85, "return_temp_c": 55}
    
    # Create mock result
    mock_result = {
        "success": True,
        "kpi": {"total_heat_supplied_mwh": 234.5},
        "execution_time_s": 4.5
    }
    
    # Set cache
    cache.set("DH", sample_buildings, params, mock_result)
    assert cache.stats["sets"] == 1
    
    # Get from cache
    cached_result = cache.get("DH", sample_buildings, params)
    
    assert cached_result is not None
    assert cached_result["success"] == True
    assert cached_result["kpi"]["total_heat_supplied_mwh"] == 234.5
    assert cache.stats["hits"] == 1


def test_cache_key_consistency(temp_cache_dir, sample_buildings):
    """Test that same inputs generate same cache key."""
    cache = SimulationCache(cache_dir=temp_cache_dir)
    
    params = {"supply_temp_c": 85, "return_temp_c": 55}
    
    key1 = cache._get_cache_key("DH", ["B001", "B002", "B003"], params)
    key2 = cache._get_cache_key("DH", ["B003", "B002", "B001"], params)  # Different order
    
    # Should be same (buildings are sorted)
    assert key1 == key2


def test_cache_key_uniqueness(temp_cache_dir):
    """Test that different inputs generate different cache keys."""
    cache = SimulationCache(cache_dir=temp_cache_dir)
    
    params1 = {"supply_temp_c": 85}
    params2 = {"supply_temp_c": 90}  # Different temp
    
    key1 = cache._get_cache_key("DH", ["B001", "B002"], params1)
    key2 = cache._get_cache_key("DH", ["B001", "B002"], params2)
    
    # Should be different
    assert key1 != key2


def test_cache_clear(temp_cache_dir, sample_buildings):
    """Test clearing cache."""
    cache = SimulationCache(cache_dir=temp_cache_dir)
    
    # Add some cached results
    params = {"supply_temp_c": 85}
    mock_result = {"success": True}
    
    cache.set("DH", sample_buildings, params, mock_result)
    cache.set("HP", sample_buildings, params, mock_result)
    
    # Clear DH cache only
    deleted = cache.clear("DH")
    assert deleted >= 2  # .pkl and _meta.json
    
    # DH should be empty, HP should still have files
    dh_files = list((cache.cache_dir / "dh").glob("*"))
    hp_files = list((cache.cache_dir / "hp").glob("*"))
    
    assert len(dh_files) == 0
    assert len(hp_files) >= 2


def test_cache_statistics(temp_cache_dir, sample_buildings):
    """Test cache statistics tracking."""
    cache = SimulationCache(cache_dir=temp_cache_dir)
    
    params = {"supply_temp_c": 85}
    mock_result = {"success": True}
    
    # Miss
    cache.get("DH", sample_buildings, params)
    
    # Set
    cache.set("DH", sample_buildings, params, mock_result)
    
    # Hit
    cache.get("DH", sample_buildings, params)
    
    stats = cache.get_stats()
    
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["sets"] == 1
    assert stats["total_requests"] == 2
    assert stats["hit_rate_pct"] == 50.0


if __name__ == "__main__":
    """Run tests directly."""
    print("Running Cache Manager Tests...")
    print("="*60)
    
    import tempfile
    import shutil
    
    # Create temp cache dir
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # Test 1: Initialization
        print("\n1. Testing Cache Initialization")
        cache = SimulationCache(cache_dir=temp_dir)
        print("✅ Cache initialized")
        
        # Test 2: Cache miss
        print("\n2. Testing Cache Miss")
        buildings = gpd.GeoDataFrame({
            'GebaeudeID': ['B001', 'B002'],
            'heating_load_kw': [50.0, 75.0],
            'geometry': [Point(0, 0), Point(100, 0)]
        }, crs='EPSG:25833')
        
        params = {"supply_temp_c": 85}
        result = cache.get("DH", buildings, params)
        assert result is None
        print("✅ Cache miss works")
        
        # Test 3: Cache set and get
        print("\n3. Testing Cache Set and Get")
        mock_result = {"success": True, "kpi": {"heat": 234.5}}
        cache.set("DH", buildings, params, mock_result)
        
        cached = cache.get("DH", buildings, params)
        assert cached is not None
        assert cached["kpi"]["heat"] == 234.5
        print("✅ Cache set/get works")
        
        # Test 4: Statistics
        print("\n4. Testing Cache Statistics")
        stats = cache.get_stats()
        print(f"  Hits: {stats['hits']}")
        print(f"  Misses: {stats['misses']}")
        print(f"  Hit rate: {stats['hit_rate_pct']}%")
        print("✅ Statistics tracking works")
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)
    
    print("\n" + "="*60)
    print("All cache tests passed!")

