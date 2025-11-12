"""
Simulation Cache Manager

Provides intelligent caching of simulation results to avoid re-running
identical simulations. Dramatically improves performance for repeated
queries.

Features:
- MD5-based cache key generation
- TTL (time-to-live) expiration
- Separate caches for DH and HP
- Metadata tracking
- Cache statistics
"""

import hashlib
import json
import pickle
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import geopandas as gpd


class SimulationCache:
    """
    Manages caching of simulation results for performance optimization.
    
    Cache Structure:
        simulation_cache/
        ├── dh/
        │   ├── {hash}.pkl        # Pickled SimulationResult
        │   └── {hash}_meta.json  # Metadata (timestamp, inputs)
        └── hp/
            ├── {hash}.pkl
            └── {hash}_meta.json
    
    Example:
        >>> cache = SimulationCache()
        >>> result = cache.get("DH", building_ids, params)
        >>> if result is None:
        ...     result = run_simulation()
        ...     cache.set("DH", building_ids, params, result)
    """
    
    def __init__(self, cache_dir: Path = Path("simulation_cache"), ttl_hours: int = 24):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Directory to store cache files
            ttl_hours: Time-to-live in hours (default 24)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        (self.cache_dir / "dh").mkdir(exist_ok=True)
        (self.cache_dir / "hp").mkdir(exist_ok=True)
        
        self.ttl = timedelta(hours=ttl_hours)
        
        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "expired": 0,
        }
    
    def _get_cache_key(self, simulation_type: str, building_ids: List[str], params: Dict[str, Any]) -> str:
        """
        Generate unique cache key from simulation inputs.
        
        Args:
            simulation_type: "DH" or "HP"
            building_ids: List of building identifiers
            params: Simulation parameters
        
        Returns:
            32-character hexadecimal hash
        """
        # Create cache key data
        cache_data = {
            "type": simulation_type,
            "buildings": sorted(building_ids),  # Sort for consistency
            "params": params
        }
        
        # Generate MD5 hash
        key_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _get_building_ids(self, buildings_gdf: gpd.GeoDataFrame) -> List[str]:
        """Extract building IDs from GeoDataFrame."""
        if "GebaeudeID" in buildings_gdf.columns:
            return sorted(buildings_gdf["GebaeudeID"].tolist())
        elif "building_id" in buildings_gdf.columns:
            return sorted(buildings_gdf["building_id"].tolist())
        else:
            # Use index as fallback
            return sorted([str(idx) for idx in buildings_gdf.index])
    
    def get(self, 
            simulation_type: str, 
            buildings_gdf: gpd.GeoDataFrame, 
            params: Dict[str, Any]) -> Optional[Any]:
        """
        Retrieve cached simulation result if available and valid.
        
        Args:
            simulation_type: "DH" or "HP"
            buildings_gdf: Building data (used to extract IDs)
            params: Simulation parameters
        
        Returns:
            Cached SimulationResult if found and valid, None otherwise
        """
        building_ids = self._get_building_ids(buildings_gdf)
        key = self._get_cache_key(simulation_type, building_ids, params)
        
        cache_file = self.cache_dir / simulation_type.lower() / f"{key}.pkl"
        meta_file = self.cache_dir / simulation_type.lower() / f"{key}_meta.json"
        
        # Check if cache files exist
        if not cache_file.exists() or not meta_file.exists():
            self.stats["misses"] += 1
            return None
        
        # Load metadata and check TTL
        try:
            with open(meta_file, 'r') as f:
                metadata = json.load(f)
            
            cached_time = datetime.fromisoformat(metadata["timestamp"])
            
            if datetime.now() - cached_time > self.ttl:
                self.stats["expired"] += 1
                print(f"  ⏰ Cache EXPIRED: {key} (age: {(datetime.now() - cached_time).total_seconds()/3600:.1f}h)")
                return None
            
        except Exception as e:
            print(f"  ⚠️  Cache metadata error: {e}")
            self.stats["misses"] += 1
            return None
        
        # Load cached result
        try:
            with open(cache_file, 'rb') as f:
                result = pickle.load(f)
            
            self.stats["hits"] += 1
            age_hours = (datetime.now() - cached_time).total_seconds() / 3600
            print(f"  💾 Cache HIT: {key} (age: {age_hours:.1f}h, saved {metadata.get('execution_time_s', 0):.1f}s)")
            
            return result
            
        except Exception as e:
            print(f"  ⚠️  Cache load error: {e}")
            self.stats["misses"] += 1
            return None
    
    def set(self, 
            simulation_type: str, 
            buildings_gdf: gpd.GeoDataFrame, 
            params: Dict[str, Any], 
            result: Any) -> None:
        """
        Store simulation result in cache.
        
        Args:
            simulation_type: "DH" or "HP"
            buildings_gdf: Building data (used to extract IDs)
            params: Simulation parameters
            result: SimulationResult to cache
        """
        building_ids = self._get_building_ids(buildings_gdf)
        key = self._get_cache_key(simulation_type, building_ids, params)
        
        cache_file = self.cache_dir / simulation_type.lower() / f"{key}.pkl"
        meta_file = self.cache_dir / simulation_type.lower() / f"{key}_meta.json"
        
        try:
            # Save result
            with open(cache_file, 'wb') as f:
                pickle.dump(result, f)
            
            # Save metadata
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "simulation_type": simulation_type,
                "num_buildings": len(building_ids),
                "cache_key": key,
                "execution_time_s": getattr(result, 'execution_time_s', 0),
            }
            
            with open(meta_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.stats["sets"] += 1
            print(f"  💾 Cached: {key}")
            
        except Exception as e:
            print(f"  ⚠️  Cache save error: {e}")
    
    def clear(self, simulation_type: Optional[str] = None) -> int:
        """
        Clear cache for specific type or all types.
        
        Args:
            simulation_type: "DH", "HP", or None for all
        
        Returns:
            Number of files deleted
        """
        deleted = 0
        
        if simulation_type:
            cache_subdir = self.cache_dir / simulation_type.lower()
            for file in cache_subdir.glob("*"):
                file.unlink()
                deleted += 1
            print(f"  🗑️  Cleared {deleted} files from {simulation_type} cache")
        else:
            for file in self.cache_dir.rglob("*"):
                if file.is_file():
                    file.unlink()
                    deleted += 1
            print(f"  🗑️  Cleared all cache ({deleted} files)")
        
        return deleted
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with hit/miss/set counts
        """
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.stats,
            "total_requests": total_requests,
            "hit_rate_pct": round(hit_rate, 1)
        }
    
    def print_stats(self):
        """Print cache statistics."""
        stats = self.get_stats()
        
        print("\n  📊 Cache Statistics:")
        print(f"     Hits:     {stats['hits']}")
        print(f"     Misses:   {stats['misses']}")
        print(f"     Sets:     {stats['sets']}")
        print(f"     Expired:  {stats['expired']}")
        print(f"     Hit Rate: {stats['hit_rate_pct']}%")
    
    def get_cache_size(self) -> Dict[str, int]:
        """
        Get cache size information.
        
        Returns:
            Dictionary with file counts and sizes
        """
        dh_files = list((self.cache_dir / "dh").glob("*.pkl"))
        hp_files = list((self.cache_dir / "hp").glob("*.pkl"))
        
        dh_size = sum(f.stat().st_size for f in dh_files)
        hp_size = sum(f.stat().st_size for f in hp_files)
        
        return {
            "dh_entries": len(dh_files),
            "hp_entries": len(hp_files),
            "dh_size_mb": round(dh_size / 1024 / 1024, 2),
            "hp_size_mb": round(hp_size / 1024 / 1024, 2),
            "total_size_mb": round((dh_size + hp_size) / 1024 / 1024, 2),
        }

