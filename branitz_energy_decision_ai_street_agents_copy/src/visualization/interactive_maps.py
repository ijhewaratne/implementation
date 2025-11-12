"""
Interactive HTML map generation with Folium.

This module creates interactive web-based maps with:
- Temperature/voltage color gradients
- Clickable network elements
- Hover tooltips with detailed KPIs
- Layer controls
- Performance dashboards
- Statistics panels

Adapted from street_final_copy_3/04_create_pandapipes_interactive_map.py
"""

import folium
from folium import plugins
import numpy as np
import pandas as pd
import geopandas as gpd
import json
from pathlib import Path
from shapely.geometry import mapping, LineString, Point
from typing import Optional, Dict, Any, List, Union

from .colormaps import NETWORK_COLORS, get_temperature_color, get_voltage_color, get_loading_color


class InteractiveMapGenerator:
    """
    Generate interactive HTML maps with color-coded cascading visualizations.
    
    Uses Folium (Leaflet.js) to create web-based interactive maps.
    """
    
    def __init__(self, output_dir: str = "results_test/visualizations/interactive"):
        """
        Initialize the interactive map generator.
        
        Args:
            output_dir: Directory to save generated HTML maps
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def create_dh_interactive_map(
        self,
        scenario_name: str,
        net=None,
        buildings_gdf: Optional[gpd.GeoDataFrame] = None,
        kpi: Optional[Dict[str, Any]] = None,
        dual_topology: Optional[Dict[str, Any]] = None,
        thermal_profile: Optional[List[Dict[str, Any]]] = None,
        routing_analysis: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create interactive DH map with temperature cascading colors.
        
        Args:
            net: pandapipes network object
            scenario_name: Name of the scenario
            buildings_gdf: Optional building geometries
            kpi: Optional KPI dictionary
        
        Returns:
            Path to saved HTML file
        """
        if dual_topology is None and net is None:
            raise ValueError("Either 'net' or 'dual_topology' must be provided for DH map generation")

        # Find center point for the map
        if dual_topology is not None:
            center_lat, center_lon = self._find_topology_center(dual_topology)
        else:
            center_lat, center_lon = self._find_network_center(net)
        
        # Create base map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=16,
            tiles="OpenStreetMap"
        )
        
        # Add alternative tile layers
        folium.TileLayer("cartodbpositron", name="CartoDB Positron").add_to(m)
        
        # Create feature groups for layer control
        supply_group = folium.FeatureGroup(name="Supply Mains (hot)", overlay=True)
        return_group = folium.FeatureGroup(name="Return Mains (cold)", overlay=True)
        service_group = folium.FeatureGroup(name="Service Connections", overlay=True)
        junction_group = folium.FeatureGroup(name="Network Junctions", overlay=True)
        consumer_group = folium.FeatureGroup(name="Heat Consumers", overlay=True)
        plant_group = folium.FeatureGroup(name="CHP Plant", overlay=True)
        
        if dual_topology is not None:
            self._add_dual_pipes(dual_topology, supply_group, return_group)
            self._add_dual_service_connections(dual_topology, service_group)
            self._add_dual_junctions(m, dual_topology, junction_group)
            self._add_dual_consumers(m, dual_topology, consumer_group)
            self._add_dual_plant(m, dual_topology, plant_group)
        else:
            self._add_supply_pipes(m, net, supply_group)
            self._add_return_pipes(m, net, return_group)
            self._add_junctions(m, net, junction_group)
            self._add_heat_consumers(m, net, consumer_group)
            self._add_chp_plant(m, net, plant_group)
        
        # Add all feature groups
        supply_group.add_to(m)
        return_group.add_to(m)
        service_group.add_to(m)
        junction_group.add_to(m)
        consumer_group.add_to(m)
        plant_group.add_to(m)
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        # Add network statistics panel
        if kpi:
            self._add_network_statistics(m, kpi)
            self._add_performance_dashboard(m, kpi)
        
        if dual_topology and routing_analysis:
            self._add_routing_summary(m, dual_topology, routing_analysis)
        elif dual_topology:
            self._add_routing_summary(m, dual_topology, {})
        
        if thermal_profile:
            self._add_thermal_panel(m, thermal_profile)
        
        # Add legend
        self._add_dh_legend(m)
        
        # Save map
        html_file = self.output_dir / f"{scenario_name}_dh_interactive.html"
        m.save(str(html_file))
        
        print(f"✅ DH interactive map saved: {html_file}")
        return str(html_file)
    
    def create_hp_interactive_map(
        self,
        scenario_name: str,
        buildings_gdf: Optional[gpd.GeoDataFrame] = None,
        kpi: Optional[Dict[str, Any]] = None,
        *,
        buses_data: Optional[Union[str, Path, gpd.GeoDataFrame]] = None,
        lines_data: Optional[Union[str, Path, gpd.GeoDataFrame]] = None,
        violations_data: Optional[Union[str, Path, pd.DataFrame]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        output_path: Optional[Path] = None,
    ) -> str:
        """Create an interactive HP map mirroring legacy LV visualization."""
        buses_gdf = self._load_hp_geodata(buses_data)
        lines_gdf = self._load_hp_geodata(lines_data)
        violations_df = self._load_hp_violations(violations_data)

        buildings_latlon = self._ensure_latlon_gdf(buildings_gdf)

        center_lat, center_lon = self._compute_hp_center(buses_gdf, lines_gdf, buildings_latlon)

        m = folium.Map(location=[center_lat, center_lon], zoom_start=16, tiles=None, control_scale=True)
        folium.TileLayer(
            tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
            attr="&copy; <a href='https://www.openstreetmap.org/copyright'>OSM</a> contributors &amp; CARTO",
            name="CartoDB Positron",
        ).add_to(m)
        folium.TileLayer(
            tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            attr="&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors",
            name="OpenStreetMap",
        ).add_to(m)
        folium.TileLayer(
            tiles="https://stamen-tiles.a.ssl.fastly.net/toner/{z}/{x}/{y}.png",
            attr="Map tiles by <a href='http://stamen.com'>Stamen Design</a>, CC BY 3.0",
            name="Stamen Toner",
        ).add_to(m)

        voltage_group = folium.FeatureGroup(name="LV Buses (Voltage)", overlay=True)
        line_group = folium.FeatureGroup(name="LV Lines (Loading)", overlay=True)
        violation_group = folium.FeatureGroup(name="Alerts", overlay=True, show=False)
        transformer_group = folium.FeatureGroup(name="Transformer", overlay=True, show=True)
        building_group = folium.FeatureGroup(name="Buildings", overlay=False, show=False)

        if lines_gdf is not None and not lines_gdf.empty:
            self._add_hp_lines(lines_gdf, line_group)
            line_group.add_to(m)

        if buses_gdf is not None and not buses_gdf.empty:
            self._add_hp_buses(buses_gdf, voltage_group)
            voltage_group.add_to(m)

        if not violations_df.empty:
            self._add_hp_violations(violations_df, buses_gdf, lines_gdf, violation_group)
            if len(violation_group._children) > 0:  # type: ignore[attr-defined]
                violation_group.add_to(m)

        transformer_id = None
        if metadata:
            transformer_id = metadata.get("transformer_location")
        if transformer_id is not None and buses_gdf is not None and not buses_gdf.empty:
            self._add_hp_transformer_marker(transformer_id, buses_gdf, transformer_group)
            if len(transformer_group._children) > 0:  # type: ignore[attr-defined]
                transformer_group.add_to(m)

        if buildings_latlon is not None and not buildings_latlon.empty:
            self._add_buildings_layer(buildings_latlon, building_group)
            building_group.add_to(m)

        folium.LayerControl().add_to(m)

        title = metadata.get("street_name") if metadata else None
        self._add_hp_info_panel(
            m,
            title=title or scenario_name,
            kpi=kpi,
            buses_gdf=buses_gdf,
            lines_gdf=lines_gdf,
        )
        self._add_hp_legend(m)

        html_file = output_path if output_path is not None else self.output_dir / f"{scenario_name}_hp_interactive.html"
        html_file = Path(html_file)
        html_file.parent.mkdir(parents=True, exist_ok=True)
        m.save(str(html_file))

        print(f"✅ HP interactive map saved: {html_file}")
        return str(html_file)
    
    def _load_hp_geodata(
        self,
        data: Optional[Union[str, Path, gpd.GeoDataFrame]],
    ) -> Optional[gpd.GeoDataFrame]:
        if data is None:
            return None
        if isinstance(data, gpd.GeoDataFrame):
            gdf = data.copy()
        else:
            path = Path(data)
            if not path.exists():
                return None
            gdf = gpd.read_file(path)
        return self._ensure_latlon_gdf(gdf)

    def _load_hp_violations(
        self,
        data: Optional[Union[str, Path, pd.DataFrame]],
    ) -> pd.DataFrame:
        if data is None:
            return pd.DataFrame()
        if isinstance(data, pd.DataFrame):
            return data.copy()
        path = Path(data)
        if not path.exists():
            return pd.DataFrame()
        try:
            return pd.read_csv(path)
        except Exception:
            return pd.DataFrame()

    def _ensure_latlon_gdf(
        self,
        gdf: Optional[gpd.GeoDataFrame],
        default_epsg: int = 32633,
    ) -> Optional[gpd.GeoDataFrame]:
        if gdf is None or gdf.empty:
            return gdf
        local_gdf = gdf.copy()
        if local_gdf.crs is None:
            try:
                local_gdf = local_gdf.set_crs(epsg=default_epsg, allow_override=True)
            except TypeError:
                local_gdf = local_gdf.set_crs(epsg=default_epsg)
        try:
            current_epsg = local_gdf.crs.to_epsg() if local_gdf.crs is not None else None
        except AttributeError:
            current_epsg = None
        if current_epsg != 4326:
            local_gdf = local_gdf.to_crs(epsg=4326)
        if "id" in local_gdf.columns:
            try:
                local_gdf["id"] = local_gdf["id"].astype(int)
            except Exception:
                pass
        return local_gdf

    def _compute_hp_center(
        self,
        buses_gdf: Optional[gpd.GeoDataFrame],
        lines_gdf: Optional[gpd.GeoDataFrame],
        buildings_gdf: Optional[gpd.GeoDataFrame],
    ) -> tuple:
        for candidate in (buses_gdf, lines_gdf, buildings_gdf):
            if candidate is not None and not candidate.empty:
                geom = candidate.geometry
                if geom.geom_type.isin(["Point", "MultiPoint"]).all():
                    return geom.y.mean(), geom.x.mean()
                centroid = geom.unary_union.centroid
                return centroid.y, centroid.x
        return 51.76274, 14.3453979

    def _add_hp_lines(self, lines_gdf: gpd.GeoDataFrame, line_group: folium.FeatureGroup) -> None:
        for _, line_row in lines_gdf.iterrows():
            geom = line_row.geometry
            if geom is None or geom.is_empty:
                continue
            if geom.geom_type == "MultiLineString":
                coord_sets = []
                for part in geom.geoms:
                    coord_sets.extend([[lat, lon] for lon, lat in part.coords])
                coords = coord_sets
            else:
                coords = [[lat, lon] for lon, lat in geom.coords]
            loading_pct = float(line_row.get("loading_pct", 0.0))
            color = get_loading_color(loading_pct)
            status = str(line_row.get("loading_status", "")).title()
            weight = max(3.0, min(10.0, 3.0 + (loading_pct / 18.0)))
            popup_lines = [
                f"<strong>Line {line_row.get('id', '')}</strong>",
                f"Name: {line_row.get('name', 'n/a')}",
                f"Length: {float(line_row.get('length_m', 0)):.0f} m",
                f"Loading: {loading_pct:.1f}%",
            ]
            current = line_row.get("current_i_ka")
            if pd.notna(current):
                popup_lines.append(f"Current: {float(current):.3f} kA")
            max_i = line_row.get("max_i_ka")
            if pd.notna(max_i) and float(max_i) > 0:
                popup_lines.append(f"Max Current: {float(max_i):.3f} kA")
            if status:
                popup_lines.append(f"Status: {status}")
            tooltip_html = "<br>".join(popup_lines)
            folium.PolyLine(
                locations=coords,
                color=color,
                weight=weight,
                opacity=0.9,
                tooltip=tooltip_html,
                popup=tooltip_html,
            ).add_to(line_group)

    def _add_hp_buses(self, buses_gdf: gpd.GeoDataFrame, voltage_group: folium.FeatureGroup) -> None:
        if "voltage_pu" not in buses_gdf.columns:
            return
        for _, bus_row in buses_gdf.iterrows():
            geom = bus_row.geometry
            if geom is None or geom.is_empty:
                continue
            load_kw = float(bus_row.get("load_kw", 0.0))
            has_load = bool(bus_row.get("has_load", False) or load_kw > 1e-3)
            is_transformer = bool(bus_row.get("is_transformer", False))
            if not has_load and not is_transformer:
                continue
            lat, lon = geom.y, geom.x
            voltage = float(bus_row.get("voltage_pu", 0.0))
            color = get_voltage_color(voltage)
            voltage_status = str(bus_row.get("voltage_status", "")).title()
            popup_lines = [
                f"<strong>Bus {bus_row.get('id', '')}</strong>",
                f"Name: {bus_row.get('name', 'n/a')}",
                f"Voltage: {voltage:.3f} pu",
            ]
            voltage_kv = bus_row.get("voltage_kv")
            if pd.notna(voltage_kv):
                popup_lines.append(f"Base Voltage: {float(voltage_kv):.3f} kV")
            if load_kw > 0:
                popup_lines.append(f"Load: {load_kw:.1f} kW")
            if voltage_status:
                popup_lines.append(f"Status: {voltage_status}")
            tooltip_html = "<br>".join(popup_lines)
            marker_radius = 6 + min(8, load_kw / 40.0) if load_kw > 0 else 7
            border_color = "#003366" if is_transformer else "#000000"
            border_weight = 2 if is_transformer else 1
            folium.CircleMarker(
                location=[lat, lon],
                radius=marker_radius,
                color=border_color,
                weight=border_weight,
                fill=True,
                fill_color=color,
                fill_opacity=0.95,
                tooltip=tooltip_html,
                popup=tooltip_html,
            ).add_to(voltage_group)

    def _add_hp_violations(
        self,
        violations_df: pd.DataFrame,
        buses_gdf: Optional[gpd.GeoDataFrame],
        lines_gdf: Optional[gpd.GeoDataFrame],
        violation_group: folium.FeatureGroup,
    ) -> None:
        if violations_df.empty:
            return
        lines_lookup = None
        buses_lookup = None
        if lines_gdf is not None and not lines_gdf.empty:
            lines_lookup = lines_gdf.set_index("id")
        if buses_gdf is not None and not buses_gdf.empty:
            buses_lookup = buses_gdf.set_index("id")
        for _, row in violations_df.iterrows():
            element = str(row.get("element", ""))
            severity = row.get("severity", "warning")
            color = NETWORK_COLORS['critical'] if severity == "critical" else NETWORK_COLORS['warning']
            if element.startswith("line_") and lines_lookup is not None:
                try:
                    line_id = int(element.split("_")[-1])
                except ValueError:
                    continue
                if line_id not in lines_lookup.index:
                    continue
                geom = lines_lookup.loc[line_id].geometry
                coords = [[lat, lon] for lon, lat in geom.coords]
                folium.PolyLine(
                    locations=coords,
                    color=color,
                    weight=7,
                    opacity=0.95,
                    tooltip=f"Line {line_id}: {row.get('value', '')} (limit {row.get('limit', '')})",
                ).add_to(violation_group)
            elif element.startswith("bus_") and buses_lookup is not None:
                try:
                    bus_id = int(element.split("_")[-1])
                except ValueError:
                    continue
                if bus_id not in buses_lookup.index:
                    continue
                geom = buses_lookup.loc[bus_id].geometry
                folium.CircleMarker(
                    location=[geom.y, geom.x],
                    radius=8,
                    color=color,
                    weight=2,
                    fill=False,
                    tooltip=f"Bus {bus_id}: {row.get('value', '')} (limit {row.get('limit', '')})",
                ).add_to(violation_group)

    def _add_hp_transformer_marker(
        self,
        transformer_id: Any,
        buses_gdf: gpd.GeoDataFrame,
        transformer_group: folium.FeatureGroup,
    ) -> None:
        try:
            transformer_id = int(transformer_id)
        except (TypeError, ValueError):
            return
        match = buses_gdf[buses_gdf["id"] == transformer_id]
        if match.empty:
            return
        geom = match.iloc[0].geometry
        folium.Marker(
            location=[geom.y, geom.x],
            icon=folium.Icon(color="orange", icon="bolt", prefix="fa"),
            tooltip=f"Transformer Bus {transformer_id}",
        ).add_to(transformer_group)

    def _add_buildings_layer(self, buildings_gdf: gpd.GeoDataFrame, building_group: folium.FeatureGroup) -> None:
        for _, building in buildings_gdf.iterrows():
            geom = building.geometry
            if geom is None:
                continue
            centroid = geom.centroid
            folium.CircleMarker(
                location=[centroid.y, centroid.x],
                radius=4,
                color=NETWORK_COLORS['building_outline'],
                weight=1,
                fill=True,
                fill_color=NETWORK_COLORS['building'],
                fill_opacity=0.5,
                tooltip=str(building.get('GebaeudeID', 'Building')),
            ).add_to(building_group)

    def _add_hp_info_panel(
        self,
        m: folium.Map,
        title: str,
        kpi: Optional[Dict[str, Any]],
        buses_gdf: Optional[gpd.GeoDataFrame],
        lines_gdf: Optional[gpd.GeoDataFrame],
    ) -> None:
        min_voltage = kpi.get("min_voltage_pu") if kpi else None
        max_loading = kpi.get("max_line_loading_pct") if kpi else None
        transformer_loading = kpi.get("transformer_loading_pct") if kpi else None
        min_voltage_html = f"{min_voltage:.3f} pu" if min_voltage is not None else "—"
        max_loading_html = f"{max_loading:.1f}%" if max_loading is not None else "—"
        transformer_loading_html = (
            f"{transformer_loading:.1f}%" if transformer_loading is not None else "—"
        )
        voltage_list_html = ""
        if buses_gdf is not None and not buses_gdf.empty and "voltage_pu" in buses_gdf.columns:
            worst_buses = buses_gdf.nsmallest(6, "voltage_pu")
            rows = []
            for _, bus in worst_buses.iterrows():
                rows.append(
                    f"<tr><td>Bus {bus.get('id')}</td><td>{float(bus.get('voltage_pu', 0.0)):.3f} pu</td></tr>"
                )
            voltage_list_html = "".join(rows)
        loading_list_html = ""
        if lines_gdf is not None and not lines_gdf.empty and "loading_pct" in lines_gdf.columns:
            worst_lines = lines_gdf.nlargest(6, "loading_pct")
            rows = []
            for _, line in worst_lines.iterrows():
                rows.append(
                    f"<tr><td>Line {line.get('id')}</td><td>{float(line.get('loading_pct', 0.0)):.1f}%</td></tr>"
                )
            loading_list_html = "".join(rows)
        kpi_html = f"""
        <div style="position: fixed; top: 20px; left: 20px; width: 320px; background-color: white; border:2px solid grey; z-index:9999; padding: 12px; border-radius: 6px; font-size:12px;">
            <h3 style="margin-top: 0; font-size:16px;">{title}</h3>
            <p style="margin:0 0 8px 0; font-size:12px;">Heat Pump LV Grid Analysis</p>
            <table style="width:100%; font-size:12px;">
                <tr><th align="left">Min Voltage</th><td>{min_voltage_html}</td></tr>
                <tr><th align="left">Max Line Loading</th><td>{max_loading_html}</td></tr>
                <tr><th align="left">Transformer Loading</th><td>{transformer_loading_html}</td></tr>
            </table>
            <div style="margin-top:8px; display:flex; gap:4px;">
                <div style="flex:1;">
                    <strong>Lowest Voltages</strong>
                    <table style="width:100%; font-size:11px;">{voltage_list_html}</table>
                </div>
                <div style="flex:1;">
                    <strong>Highest Loadings</strong>
                    <table style="width:100%; font-size:11px;">{loading_list_html}</table>
                </div>
            </div>
        </div>
        """
        m.get_root().html.add_child(folium.Element(kpi_html))
    
    # ========================================================================
    # Helper Methods - DH Network Elements
    # ========================================================================
    
    def _find_network_center(self, net) -> tuple:
        """Find center coordinates of network for map centering."""
        center_x, center_y = 0, 0
        count = 0
        
        for idx, junction in net.junction.iterrows():
            try:
                if hasattr(junction, "geodata") and junction.geodata is not None:
                    x, y = junction.geodata[0], junction.geodata[1]
                else:
                    x, y = junction.x, junction.y
                
                # Convert to lat/lon if in projected CRS
                from pyproj import Transformer
                transformer = Transformer.from_crs("EPSG:25833", "EPSG:4326", always_xy=True)
                lon, lat = transformer.transform(x, y)
                
                center_x += lon
                center_y += lat
                count += 1
            except Exception:
                continue
        
        if count > 0:
            center_x /= count
            center_y /= count
        else:
            # Default to Cottbus
            center_x, center_y = 14.3453979, 51.76274
        
        return center_y, center_x
    
    def _find_topology_center(self, topology: Dict[str, Any]) -> tuple:
        """Compute map center from dual topology coordinates."""
        from pyproj import Transformer

        transformer = Transformer.from_crs("EPSG:32633", "EPSG:4326", always_xy=True)
        lat_sum = 0.0
        lon_sum = 0.0
        count = 0

        for junction in topology.get("junctions", []):
            lon, lat = transformer.transform(junction["x"], junction["y"])
            lat_sum += lat
            lon_sum += lon
            count += 1

        if count > 0:
            return lat_sum / count, lon_sum / count
        plant = topology.get("plant")
        if plant:
            lon, lat = transformer.transform(plant["x"], plant["y"])
            return lat, lon
        return 51.76274, 14.3453979
    
    def _add_supply_pipes(self, m, net, supply_group):
        """Add supply pipes to map (red for hot)."""
        try:
            for i, row in net.pipe_geodata.iterrows():
                if row.name.startswith("SUP_"):
                    geom = LineString(row.coords)
                    
                    # Transform coordinates
                    from pyproj import Transformer
                    transformer = Transformer.from_crs("EPSG:25833", "EPSG:4326", always_xy=True)
                    
                    coords = list(geom.coords)
                    transformed_coords = [transformer.transform(x, y) for x, y in coords]
                    latlon_coords = [[lat, lon] for lon, lat in transformed_coords]
                    
                    folium.PolyLine(
                        locations=latlon_coords,
                        color=NETWORK_COLORS['supply_pipe'],
                        weight=4,
                        opacity=0.8,
                        popup=f"Supply Pipe: {row.name}",
                        tooltip="Supply Pipe (hot)"
                    ).add_to(supply_group)
        except Exception as e:
            print(f"⚠️  Could not add supply pipes: {e}")
    
    def _add_dual_pipes(self, topology: Dict[str, Any], supply_group, return_group):
        """Add dual-pipe supply/return polylines from topology."""
        from pyproj import Transformer

        transformer = Transformer.from_crs("EPSG:32633", "EPSG:4326", always_xy=True)

        for pipe in topology.get("pipes", []):
            coords = pipe.get("coords", [])
            if not coords:
                continue

            transformed = [transformer.transform(x, y) for x, y in coords]
            latlon_coords = [[lat, lon] for lon, lat in transformed]

            is_supply = pipe.get("type") == "supply"
            base_color = NETWORK_COLORS['supply_pipe'] if is_supply else NETWORK_COLORS['return_pipe']
            color = base_color

            diameter_m = pipe.get("diameter_m")
            diameter_mm = diameter_m * 1000 if diameter_m else None
            velocity = pipe.get("velocity_ms")
            pressure_drop = pipe.get("pressure_drop_pa_per_m")
            compliant = pipe.get("standards_compliant")

            base_weight = 4 if is_supply else 3
            if diameter_mm:
                base_weight += diameter_mm / 150.0
            weight = max(2.5, min(12.0, base_weight))

            if compliant is False:
                color = "#B22222"

            opacity = 0.85 if is_supply else 0.7
            length_m = LineString(coords).length
            pipe_label = "Supply" if is_supply else "Return"
            details = [
                f"<strong>{pipe_label} Pipe</strong>: {pipe.get('id', 'pipe')}",
                f"Length: {length_m:.1f} m",
            ]
            if diameter_mm:
                dn = pipe.get("diameter_dn", "")
                dn_text = f" (DN {dn})" if dn else ""
                details.append(f"Diameter: {diameter_mm:.0f} mm{dn_text}")
            if velocity is not None:
                details.append(f"Velocity: {velocity:.2f} m/s")
            if pressure_drop is not None:
                details.append(f"Δp: {pressure_drop:.0f} Pa/m")
            if compliant is True:
                details.append("Compliance: ✅")
            elif compliant is False:
                details.append("Compliance: ❌")

            tooltip = "<br>".join(details)
            target_group = supply_group if is_supply else return_group

            folium.PolyLine(
                locations=latlon_coords,
                color=color,
                weight=weight,
                opacity=opacity,
                tooltip=tooltip,
                popup=tooltip,
            ).add_to(target_group)
    
    def _add_return_pipes(self, m, net, return_group):
        """Add return pipes to map (blue for cold)."""
        try:
            for i, row in net.pipe_geodata.iterrows():
                if not row.name.startswith("SUP_"):
                    geom = LineString(row.coords)
                    
                    # Transform coordinates
                    from pyproj import Transformer
                    transformer = Transformer.from_crs("EPSG:25833", "EPSG:4326", always_xy=True)
                    
                    coords = list(geom.coords)
                    transformed_coords = [transformer.transform(x, y) for x, y in coords]
                    latlon_coords = [[lat, lon] for lon, lat in transformed_coords]
                    
                    folium.PolyLine(
                        locations=latlon_coords,
                        color=NETWORK_COLORS['return_pipe'],
                        weight=3,
                        opacity=0.6,
                        popup=f"Return Pipe: {row.name}",
                        tooltip="Return Pipe (cold)"
                    ).add_to(return_group)
        except Exception as e:
            print(f"⚠️  Could not add return pipes: {e}")
    
    def _add_junctions(self, m, net, junction_group):
        """Add junction markers to map."""
        try:
            from pyproj import Transformer
            transformer = Transformer.from_crs("EPSG:25833", "EPSG:4326", always_xy=True)
            
            for j, row in net.junction.iterrows():
                try:
                    if hasattr(row, "geodata") and row.geodata is not None:
                        x, y = row.geodata[0], row.geodata[1]
                    else:
                        x, y = row.x, row.y
                    
                    lon, lat = transformer.transform(x, y)
                    
                    color = NETWORK_COLORS['supply_junction'] if row.name.startswith("sup_") else NETWORK_COLORS['return_junction']
                    
                    folium.CircleMarker(
                        location=[lat, lon],
                        radius=4,
                        color=color,
                        fill=True,
                        popup=f"Junction: {row.name}",
                        tooltip=f"Junction: {row.name}"
                    ).add_to(junction_group)
                except Exception:
                    continue
        except Exception as e:
            print(f"⚠️  Could not add junctions: {e}")
    
    def _add_dual_junctions(self, m, topology: Dict[str, Any], junction_group):
        """Add junction markers from dual topology."""
        from pyproj import Transformer

        transformer = Transformer.from_crs("EPSG:32633", "EPSG:4326", always_xy=True)

        for junction in topology.get("junctions", []):
            lon, lat = transformer.transform(junction["x"], junction["y"])
            if junction["type"] == "plant":
                color = NETWORK_COLORS['plant_marker'] if 'plant_marker' in NETWORK_COLORS else "green"
            else:
                color = NETWORK_COLORS['supply_junction']

            tooltip = (
                f"Junction: {junction['name']}<br>"
                f"Temperature: {junction.get('temperature', 0):.1f}°C<br>"
                f"Pressure: {junction.get('pressure', 0):.2f} bar"
            )

            folium.CircleMarker(
                location=[lat, lon],
                radius=5,
                color=color,
                fill=True,
                fillOpacity=0.8,
                tooltip=tooltip,
            ).add_to(junction_group)

    def _add_dual_service_connections(self, topology: Dict[str, Any], service_group):
        """Add service connection segments from dual topology."""
        from pyproj import Transformer

        transformer = Transformer.from_crs("EPSG:32633", "EPSG:4326", always_xy=True)

        for record in topology.get("service_connections", []):
            building_x = record.get("building_x")
            building_y = record.get("building_y")
            connection_x = record.get("connection_x") or record.get("connection_point_x")
            connection_y = record.get("connection_y") or record.get("connection_point_y")

            if None in (building_x, building_y, connection_x, connection_y):
                continue

            start_lon, start_lat = transformer.transform(building_x, building_y)
            end_lon, end_lat = transformer.transform(connection_x, connection_y)

            diameter_m = record.get("diameter_m")
            diameter_mm = diameter_m * 1000 if diameter_m else None
            velocity = record.get("velocity_ms")
            compliant = record.get("standards_compliant")

            tooltip_lines = [
                f"{record.get('pipe_type', 'service').replace('_', ' ').title()}",
                f"Building ID: {record.get('building_id')}",
                f"Distance: {record.get('distance_to_street', 0):.1f} m",
            ]
            if diameter_mm:
                dn = record.get("diameter_dn", "")
                dn_text = f" (DN {dn})" if dn else ""
                tooltip_lines.append(f"Diameter: {diameter_mm:.0f} mm{dn_text}")
            if velocity is not None:
                tooltip_lines.append(f"Velocity: {velocity:.2f} m/s")
            if compliant is False:
                tooltip_lines.append("Compliance: ❌")
            elif compliant is True:
                tooltip_lines.append("Compliance: ✅")
            tooltip = "<br>".join(tooltip_lines)

            weight = 2.0
            if diameter_mm:
                weight = max(1.5, min(6.0, 1.5 + diameter_mm / 80.0))
            color = NETWORK_COLORS.get("service_connection", "#FFA500")
            if compliant is False:
                color = "#B22222"

            folium.PolyLine(
                locations=[[start_lat, start_lon], [end_lat, end_lon]],
                color=color,
                weight=weight,
                opacity=0.9,
                tooltip=tooltip,
                popup=tooltip,
            ).add_to(service_group)
    
    def _add_heat_consumers(self, m, net, consumer_group):
        """Add heat consumer markers to map."""
        try:
            from pyproj import Transformer
            transformer = Transformer.from_crs("EPSG:25833", "EPSG:4326", always_xy=True)
            
            for hc in net.heat_consumer.itertuples():
                try:
                    sup_j = net.junction.loc[hc.from_junction]
                    if hasattr(sup_j, "geodata") and sup_j.geodata is not None:
                        x, y = sup_j.geodata[0], sup_j.geodata[1]
                    else:
                        x, y = sup_j.x, sup_j.y
                    
                    lon, lat = transformer.transform(x, y)
                    
                    folium.Marker(
                        location=[lat, lon],
                        popup=f"Heat Consumer: {hc.name}<br>Demand: {hc.qext_w/1000:.1f} kW",
                        tooltip=f"Consumer: {hc.name}",
                        icon=folium.Icon(color="orange", icon="fire", prefix="fa")
                    ).add_to(consumer_group)
                except Exception:
                    continue
        except Exception as e:
            print(f"⚠️  Could not add heat consumers: {e}")
    
    def _add_dual_consumers(self, m, topology: Dict[str, Any], consumer_group):
        """Add heat consumers using dual topology metadata."""
        from pyproj import Transformer

        transformer = Transformer.from_crs("EPSG:32633", "EPSG:4326", always_xy=True)
        junctions = {j["id"]: j for j in topology.get("junctions", [])}

        for consumer in topology.get("consumers", []):
            junction = junctions.get(consumer["junction_id"])
            if not junction:
                continue
            lon, lat = transformer.transform(junction["x"], junction["y"])
            tooltip = (
                f"Consumer: {consumer['name']}<br>"
                f"Demand: {consumer.get('heat_demand_kw', 0):.1f} kW<br>"
                f"Temperature: {consumer.get('temperature', 0):.1f}°C<br>"
                f"Pressure: {consumer.get('pressure_bar', 0):.2f} bar"
            )
            folium.Marker(
                location=[lat, lon],
                tooltip=tooltip,
                icon=folium.Icon(color="orange", icon="fire", prefix="fa"),
            ).add_to(consumer_group)
    
    def _add_dual_plant(self, m, topology: Dict[str, Any], plant_group):
        """Add plant marker from topology."""
        from pyproj import Transformer

        plant = topology.get("plant")
        if not plant:
            return

        transformer = Transformer.from_crs("EPSG:32633", "EPSG:4326", always_xy=True)
        lon, lat = transformer.transform(plant["x"], plant["y"])

        folium.Marker(
            location=[lat, lon],
            popup="CHP Plant<br>Supply Source",
            tooltip="CHP Plant",
            icon=folium.Icon(color="green", icon="industry", prefix="fa"),
        ).add_to(plant_group)
    
    def _add_chp_plant(self, m, net, plant_group):
        """Add CHP plant marker to map."""
        try:
            from pyproj import Transformer
            transformer = Transformer.from_crs("EPSG:25833", "EPSG:4326", always_xy=True)
            
            for idx, ext_grid in net.ext_grid.iterrows():
                junction = net.junction.loc[ext_grid.junction]
                if hasattr(junction, "geodata") and junction.geodata is not None:
                    x, y = junction.geodata[0], junction.geodata[1]
                else:
                    x, y = junction.x, junction.y
                
                lon, lat = transformer.transform(x, y)
                
                folium.Marker(
                    location=[lat, lon],
                    popup="CHP Plant<br>Heat Source",
                    tooltip="CHP Plant",
                    icon=folium.Icon(color="green", icon="industry", prefix="fa")
                ).add_to(plant_group)
                break
        except Exception as e:
            print(f"⚠️  Could not add CHP plant: {e}")

    def _add_routing_summary(
        self,
        m,
        topology: Dict[str, Any],
        analysis: Dict[str, Any],
    ):
        stats = topology.get("stats", {})
        total_main = analysis.get("total_main_pipe_length", stats.get("total_supply_length_m", 0) / 2)
        total_service = analysis.get("total_service_pipe_length", 0)
        success_rate = analysis.get("success_rate", stats.get("success_rate", 0))

        summary_html = f"""
        <div style="position: fixed; top: 180px; right: 10px; width: 320px;
                    background-color: white; border: 2px solid grey; z-index: 9998;
                    font-size:12px; padding: 10px; border-radius: 5px;">
            <h4 style="margin: 0 0 8px 0;">Dual-Pipe Routing Summary</h4>
            <table style="width:100%;">
                <tr><td><strong>Supply length</strong></td><td>{stats.get('total_supply_length_m', 0)/1000:.2f} km</td></tr>
                <tr><td><strong>Return length</strong></td><td>{stats.get('total_return_length_m', 0)/1000:.2f} km</td></tr>
                <tr><td><strong>Main pipes</strong></td><td>{total_main:.1f} m</td></tr>
                <tr><td><strong>Service pipes</strong></td><td>{total_service:.1f} m</td></tr>
                <tr><td><strong>Success rate</strong></td><td>{success_rate:.1f}%</td></tr>
                <tr><td><strong>Consumers</strong></td><td>{len(topology.get('consumers', []))}</td></tr>
            </table>
        </div>
        """

        m.get_root().html.add_child(folium.Element(summary_html))

    def _add_thermal_panel(self, m, thermal_profile: List[Dict[str, Any]]):
        temps = [row["temperature_c"] for row in thermal_profile]
        pressures = [row["pressure_bar"] for row in thermal_profile]

        if not temps or not pressures:
            return

        avg_temp = sum(temps) / len(temps)
        avg_pressure = sum(pressures) / len(pressures)

        thermal_html = f"""
        <div style="position: fixed; bottom: 20px; right: 10px; width: 320px;
                    background-color: #fff7e6; border: 2px solid #ffa500; z-index: 9998;
                    font-size:12px; padding: 10px; border-radius: 5px;">
            <h4 style="margin: 0 0 8px 0;">Thermal & Hydraulic Profile</h4>
            <table style="width:100%;">
                <tr><td><strong>Temperature range</strong></td><td>{min(temps):.1f}°C – {max(temps):.1f}°C</td></tr>
                <tr><td><strong>Average temperature</strong></td><td>{avg_temp:.1f}°C</td></tr>
                <tr><td><strong>Pressure range</strong></td><td>{min(pressures):.2f} – {max(pressures):.2f} bar</td></tr>
                <tr><td><strong>Average pressure</strong></td><td>{avg_pressure:.2f} bar</td></tr>
            </table>
        </div>
        """

        m.get_root().html.add_child(folium.Element(thermal_html))
    
    # ========================================================================
    # Helper Methods - Statistics & Dashboards
    # ========================================================================
    
    def _add_network_statistics(self, m, kpi: Dict[str, Any]):
        """Add network statistics panel to map."""
        stats_html = f"""
        <div style="position: fixed; 
                    top: 10px; right: 10px; width: 350px; height: auto;
                    background-color: white; border: 2px solid grey; z-index:9999; 
                    font-size:12px; padding: 10px; border-radius: 5px;">
        <h3 style="margin-top: 0;">Network Statistics</h3>
        
        <div style="background-color: #f0f8ff; padding: 10px; border-radius: 5px; margin: 5px 0;">
        <h4 style="margin: 5px 0;">Network Overview</h4>
        <table style="width: 100%;">
        <tr><td><strong>Heat Demand:</strong></td><td>{kpi.get('total_heat_supplied_mwh', 0):.2f} MWh</td></tr>
        <tr><td><strong>Buildings:</strong></td><td>{kpi.get('num_consumers', 0)}</td></tr>
        <tr><td><strong>Pipe Length:</strong></td><td>{kpi.get('total_pipe_length_km', 0):.1f} km</td></tr>
        </table>
        </div>
        
        <div style="background-color: #f0fff0; padding: 10px; border-radius: 5px; margin: 5px 0;">
        <h4 style="margin: 5px 0;">Hydraulic Performance</h4>
        <table style="width: 100%;">
        <tr><td><strong>Max Pressure Drop:</strong></td><td>{kpi.get('max_pressure_drop_bar', 0):.3f} bar</td></tr>
        <tr><td><strong>Supply Temp:</strong></td><td>{kpi.get('avg_supply_temp_c', 0):.1f}°C</td></tr>
        <tr><td><strong>Heat Losses:</strong></td><td>{kpi.get('heat_loss_percentage', 0):.1f}%</td></tr>
        </table>
        </div>
        </div>
        """
        
        m.get_root().html.add_child(folium.Element(stats_html))
    
    def _add_performance_dashboard(self, m, kpi: Dict[str, Any]):
        """Add performance dashboard to map."""
        # Calculate efficiency score
        efficiency = 100 - kpi.get('heat_loss_percentage', 10)
        efficiency_color = 'green' if efficiency > 80 else 'orange' if efficiency > 60 else 'red'
        
        dashboard_html = f"""
        <div style="position: fixed; 
                    bottom: 10px; left: 10px; width: 300px; height: auto;
                    background-color: white; border: 2px solid grey; z-index:9999; 
                    font-size:12px; padding: 10px; border-radius: 5px;">
        <h3 style="margin-top: 0;">Performance Dashboard</h3>
        
        <div style="margin: 10px 0;">
        <span>Network Efficiency:</span>
        <div style="background-color: #ddd; border-radius: 10px; height: 20px; margin: 5px 0;">
        <div style="background-color: {efficiency_color}; width: {efficiency}%; height: 100%; border-radius: 10px;"></div>
        </div>
        <span>{efficiency:.1f}%</span>
        </div>
        </div>
        """
        
        m.get_root().html.add_child(folium.Element(dashboard_html))
    
    def _add_dh_legend(self, m):
        """Add DH network legend to map."""
        legend_html = f"""
        <div style="position: fixed; 
                    bottom: 50px; right: 50px; width: 200px; height: auto; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px; border-radius: 5px;">
        <p><b>Network Legend</b></p>
        <p><span style="color:{NETWORK_COLORS['supply_pipe']};">⬤</span> Supply Pipes (hot)</p>
        <p><span style="color:{NETWORK_COLORS['return_pipe']};">⬤</span> Return Pipes (cold)</p>
        <p><span style="color:{NETWORK_COLORS['heat_consumer']};">▲</span> Heat Consumers</p>
        <p><span style="color:{NETWORK_COLORS['chp_plant']};">■</span> CHP Plant</p>
        </div>
        """
        m.get_root().html.add_child(folium.Element(legend_html))
    
    def _add_hp_legend(self, m):
        """Add HP voltage and loading legend to map."""
        legend_html = f"""
        <div style=\"position: fixed; bottom: 30px; right: 30px; width: 240px; background-color: white; border:2px solid grey; z-index:9999; font-size:12px; padding: 12px; border-radius: 6px;\">
            <h4 style=\"margin:0 0 6px 0; font-size:14px;\">Voltage Legend</h4>
            <div style=\"height:14px; background: linear-gradient(90deg,#E74C3C,#F39C12,#2ECC71); border-radius:6px;\"></div>
            <div style=\"display:flex; justify-content:space-between; font-size:11px; margin-top:2px;\">
                <span>&lt;0.92 pu</span>
                <span>0.95 pu</span>
                <span>&gt;1.05 pu</span>
            </div>
            <ul style=\"list-style:none; padding-left:0; margin:8px 0 0 0; font-size:11px;\">
                <li><span style=\"color:{NETWORK_COLORS['critical']};\">●</span> Critical (violation)</li>
                <li><span style=\"color:{NETWORK_COLORS['warning']};\">●</span> Warning (0.92-0.95 / 1.05-1.08 pu)</li>
                <li><span style=\"color:{NETWORK_COLORS['normal']};\">●</span> Normal (0.95-1.05 pu)</li>
            </ul>
            <hr style=\"margin:8px 0;\">
            <h4 style=\"margin:0 0 6px 0; font-size:14px;\">Line Loading</h4>
            <div style=\"height:14px; background: linear-gradient(90deg,#2ECC71,#F39C12,#E74C3C); border-radius:6px;\"></div>
            <div style=\"display:flex; justify-content:space-between; font-size:11px; margin-top:2px;\">
                <span>&lt;80%</span>
                <span>100%</span>
                <span>&gt;120%</span>
            </div>
        </div>
        """
        m.get_root().html.add_child(folium.Element(legend_html))

