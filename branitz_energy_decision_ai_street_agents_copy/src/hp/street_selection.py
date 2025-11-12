"""
Utilities for enumerating streets and filtering buildings for HP simulations.
"""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import geopandas as gpd
from shapely.geometry import LineString
from shapely.ops import transform, unary_union
from shapely import speedups
import pyproj

speedups.enable()  # type: ignore[attr-defined]

DEFAULT_OSM_PATH = Path("data/osm/branitzer_siedlung.osm")


@dataclass
class StreetSegment:
    way_id: int
    coordinates: List[Tuple[float, float]]  # (lon, lat)
    length_m: float
    highway_type: str


@dataclass
class StreetMetadata:
    name: str
    segments: List[StreetSegment]
    total_length_m: float
    highway_types: List[str]

    @property
    def total_length_km(self) -> float:
        return self.total_length_m / 1000.0

    @property
    def num_segments(self) -> int:
        return len(self.segments)


def _slugify(value: str) -> str:
    safe = value.strip().replace("/", "_").replace(" ", "-")
    return safe or "Unnamed"


@lru_cache(maxsize=2)
def load_osm_tree(osm_path: Path) -> ET.Element:
    if not osm_path.exists():
        raise FileNotFoundError(f"OSM file not found: {osm_path}")
    return ET.parse(str(osm_path)).getroot()


@lru_cache(maxsize=2)
def load_streets(osm_path: Path = DEFAULT_OSM_PATH) -> Dict[str, StreetMetadata]:
    root = load_osm_tree(osm_path)
    node_coords = {
        int(node.attrib["id"]): (float(node.attrib["lon"]), float(node.attrib["lat"]))
        for node in root.findall("node")
    }

    geod = pyproj.Geod(ellps="WGS84")

    streets: Dict[str, List[StreetSegment]] = {}

    for way in root.findall("way"):
        tags = {tag.attrib["k"]: tag.attrib["v"] for tag in way.findall("tag")}
        if "highway" not in tags or "name" not in tags:
            continue

        street_name = tags["name"]
        highway_type = tags.get("highway", "unknown")
        nd_refs = [int(nd.attrib["ref"]) for nd in way.findall("nd") if int(nd.attrib["ref"]) in node_coords]
        if len(nd_refs) < 2:
            continue

        coords = [node_coords[ref] for ref in nd_refs]
        lons, lats = zip(*coords)
        length_m = geod.line_length(lons, lats)

        segment = StreetSegment(
            way_id=int(way.attrib["id"]),
            coordinates=coords,
            length_m=length_m,
            highway_type=highway_type,
        )

        streets.setdefault(street_name, []).append(segment)

    metadata: Dict[str, StreetMetadata] = {}
    for name, segments in streets.items():
        total_length = sum(seg.length_m for seg in segments)
        highway_types = sorted({seg.highway_type for seg in segments})
        metadata[name] = StreetMetadata(
            name=name,
            segments=segments,
            total_length_m=total_length,
            highway_types=highway_types,
        )

    return metadata


def list_available_streets(osm_path: Path = DEFAULT_OSM_PATH) -> List[StreetMetadata]:
    return sorted(load_streets(osm_path).values(), key=lambda s: s.name)


def select_street_interactive(osm_path: Path = DEFAULT_OSM_PATH) -> Optional[str]:
    streets = list_available_streets(osm_path)
    if not streets:
        print("No streets found in OSM data.")
        return None

    print("\n" + "=" * 60)
    print("STREET SELECTION FOR HP SIMULATION")
    print("=" * 60)

    for idx, meta in enumerate(streets, start=1):
        print(f"{idx:2d}. {meta.name}")
        print(
            f"    Type: {', '.join(meta.highway_types)} | "
            f"Length: {meta.total_length_km:.2f} km | Segments: {meta.num_segments}"
        )

    print("\nOptions:")
    print("  - Enter number to select a street")
    print("  - Enter partial street name")
    print("  - Enter 'list' to show streets again")
    print("  - Enter 'quit' to exit")

    while True:
        try:
            choice = input("\nYour choice: ").strip()
        except KeyboardInterrupt:
            print("\nCancelled.")
            return None

        if choice.lower() in {"quit", "exit", "q"}:
            return None
        if choice.lower() == "list":
            for idx, meta in enumerate(streets, start=1):
                print(f"{idx:2d}. {meta.name} ({meta.total_length_km:.2f} km)")
            continue
        if not choice:
            continue

        # Numeric selection
        if choice.isdigit():
            index = int(choice)
            if 1 <= index <= len(streets):
                return streets[index - 1].name
            print(f"Enter a number between 1 and {len(streets)}")
            continue

        matches = [meta.name for meta in streets if choice.lower() in meta.name.lower()]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            print("Multiple matches found:")
            for name in matches:
                print(f"  - {name}")
            continue

        print(f"No street found matching '{choice}'. Try again.")


def _to_projected_crs(gdf: gpd.GeoDataFrame) -> Tuple[gpd.GeoDataFrame, pyproj.CRS]:
    """Project GeoDataFrame to an appropriate metric CRS."""
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    if gdf.crs.is_projected:
        return gdf, gdf.crs
    try:
        target_crs = gdf.estimate_utm_crs()
    except Exception:
        target_crs = pyproj.CRS("EPSG:32633")
    projected = gdf.to_crs(target_crs)
    return projected, target_crs


def filter_buildings_for_street(
    buildings_gdf: gpd.GeoDataFrame,
    street_meta: StreetMetadata,
    buffer_m: float = 40.0,
) -> Tuple[gpd.GeoDataFrame, Dict[str, float]]:
    """
    Filter buildings within buffer distance of the given street.

    Returns filtered GeoDataFrame (same CRS as input) and metadata.
    """
    if buildings_gdf.crs is None:
        buildings_gdf = buildings_gdf.set_crs("EPSG:4326")

    buildings_proj, target_crs = _to_projected_crs(buildings_gdf)
    transformer = pyproj.Transformer.from_crs("EPSG:4326", target_crs, always_xy=True)

    lines_proj = []
    for segment in street_meta.segments:
        line_wgs84 = LineString(segment.coordinates)
        line_proj = transform(transformer.transform, line_wgs84)
        lines_proj.append(line_proj)

    if not lines_proj:
        return buildings_gdf.iloc[0:0].copy(), {
            "street_name": street_meta.name,
            "buffer_m": buffer_m,
            "total_buildings": len(buildings_gdf),
            "filtered_buildings": 0,
            "filter_ratio": 0.0,
        }

    street_union = unary_union(lines_proj)
    buffer_area = street_union.buffer(buffer_m)

    def building_within(geom):
        if geom.is_empty:
            return False
        shape = geom
        if geom.geom_type == "Polygon":
            shape = geom.centroid
        return buffer_area.contains(shape) or buffer_area.intersects(geom)

    mask = buildings_proj.geometry.apply(building_within)
    filtered_proj = buildings_proj[mask].copy()
    filtered = filtered_proj.to_crs(buildings_gdf.crs)

    metadata = {
        "street_name": street_meta.name,
        "buffer_m": buffer_m,
        "total_buildings": int(len(buildings_gdf)),
        "filtered_buildings": int(len(filtered)),
        "filter_ratio": float(len(filtered) / len(buildings_gdf)) if len(buildings_gdf) else 0.0,
        "total_length_m": street_meta.total_length_m,
        "highway_types": street_meta.highway_types,
    }

    return filtered, metadata


