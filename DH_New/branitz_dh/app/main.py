import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st, folium
import pandas as pd
from streamlit_folium import st_folium
from dh_core.config import DHDesign, Paths
from dh_core.data_adapters import load_network_from_json, load_addresses_geojson
from dh_core.load_binding import load_design_loads_csv, match_loads_to_addresses_by_roundrobin
from dh_core.ppipe_builder import build_and_run
from dh_core.viz import gradient_layer, repaint_with_results, paint_supply_return
from dh_core.routing_osm import route_pipes_from_osm

st.set_page_config(page_title="Branitz DH", layout="wide")
st.title("Branitz District Heating – Gradients & Simulation")

# Initialize session state for persistent pandapipes results
if "pp_res_pipe" not in st.session_state: st.session_state["pp_res_pipe"] = None
if "pp_center" not in st.session_state:   st.session_state["pp_center"] = None

p = Paths()
# Use the CRS-aware JSON loader with proper de-normalization
pipes = load_network_from_json(f"{p.inputs}/network_data_with_bounds.json")
addr  = load_addresses_geojson(f"{p.inputs}/adressen_branitzer_siedlung.json")
loads = load_design_loads_csv(f"{p.inputs}/building_loads_design_mittleres.csv")
addr_with_loads = match_loads_to_addresses_by_roundrobin(loads, addr, n_points=200)

st.sidebar.header("Design Params")
design = DHDesign(
    supply_c = st.sidebar.slider("Supply °C", 60.0, 95.0, 75.0),
    return_c = st.sidebar.slider("Return °C", 30.0, 65.0, 45.0),
    u_w_per_m2k = st.sidebar.slider("Pipe U (W/m²K)", 0.10, 1.00, 0.35),
    sections = st.sidebar.slider("Pipe sections", 1, 16, 8)
)
st.sidebar.write(f"Pipes: {len(pipes)} | Address points: {len(addr)} | Points with load: {addr_with_loads['Q_design_kW'].gt(0).sum()}")

# Debug expander to verify bounds
with st.sidebar.expander("🔍 Debug Info"):
    st.write("**Network Bounds:**")
    bounds = pipes.total_bounds  # [minx, miny, maxx, maxy]
    st.write(f"Lon: {bounds[0]:.3f} to {bounds[2]:.3f}")
    st.write(f"Lat: {bounds[1]:.3f} to {bounds[3]:.3f}")
    st.write(f"CRS: {pipes.crs}")
    
    # Check if we're in Branitz region (should be ~lon 14, lat 51)
    if 14.0 <= bounds[0] <= 14.8 and 51.5 <= bounds[1] <= 52.0:
        st.success("✅ Branitz coordinates detected!")
    else:
        st.warning("⚠️ Coordinates may not be Branitz region")
    
    st.write("**Pressure Data:**")
    if 'pressure_gradient' in pipes.columns:
        st.write(f"Gradient range: {pipes['pressure_gradient'].min():.3f} to {pipes['pressure_gradient'].max():.3f}")
    if 'p_from' in pipes.columns:
        st.write(f"Pressure from: {pipes['p_from'].min():.2f} to {pipes['p_from'].max():.2f} bar")
    if 'p_to' in pipes.columns:
        st.write(f"Pressure to: {pipes['p_to'].min():.2f} to {pipes['p_to'].max():.2f} bar")


tab1, tab2, tab3 = st.tabs(["Pressure (from JSON / solve)", "Temperature (pandapipes)", "OSM Routing (demo)"])

with tab1:
    src = st.radio("Pressure source", ["JSON", "From solve"], horizontal=True)
    cent = addr.geometry.unary_union.centroid if len(addr)>0 else pipes.geometry.unary_union.centroid
    m1 = folium.Map(location=[cent.y, cent.x], zoom_start=15, tiles="cartodbpositron")
    if src == "JSON":
        gradient_layer(m1, pipes, value="pressure", diameter_col="diameter_m")  # auto limits, thin lines
    else:
        if st.session_state["pp_res_pipe"] is None:
            st.info("Run pandapipes in the Temperature tab first.")
        else:
            from dh_core.viz import repaint_with_results
            repaint_with_results(m1, pipes, st.session_state["pp_res_pipe"], layer="pressure")
    st_folium(m1, height=700, use_container_width=True)

with tab2:
    view = st.radio("Layer", ["Supply", "Return", "Both"], horizontal=True)
    if st.button("Run pandapipes"):
        with st.spinner("Solving pipeflow…"):
            net = build_and_run(
                pipes, addr_with_loads,
                design.supply_c, design.return_c,
                design.u_w_per_m2k, sections=design.sections
            )
            st.session_state["pp_res_pipe"] = net.res_pipe[["t_from_k","t_to_k","p_from_bar","p_to_bar"]].copy()
            st.session_state["pp_center"] = (cent.y, cent.x)
            st.success("Pipeflow finished.")

    if st.session_state["pp_res_pipe"] is not None:
        m2 = folium.Map(location=list(st.session_state["pp_center"] or (cent.y,cent.x)),
                        zoom_start=15, tiles="cartodbpositron")
        if view == "Both":
            from dh_core.viz import paint_supply_return
            paint_supply_return(m2, pipes, st.session_state["pp_res_pipe"], temp=True)
        else:
            from dh_core.viz import repaint_with_results
            layer = "temperature"
            repaint_with_results(m2, pipes, st.session_state["pp_res_pipe"], layer=layer)
        st_folium(m2, height=700, use_container_width=True)
    else:
        st.info("Click **Run pandapipes** to compute temperatures & repaint the map.")

with tab3:
    st.header("🌐 OSM Street-Based Pipe Routing")
    st.write("Generate a street-hugging pipe network using OpenStreetMap data and Steiner tree optimization.")
    
    # Plant location configuration
    st.subheader("🏭 Plant Location")
    plant_lat = st.number_input("Plant Latitude", value=51.737, min_value=51.0, max_value=52.0, step=0.001, format="%.3f")
    plant_lon = st.number_input("Plant Longitude", value=14.355, min_value=14.0, max_value=15.0, step=0.001, format="%.3f")
    plant_location = (plant_lat, plant_lon)
    
    # Ensure addresses have proper CRS
    if addr.crs is None:
        addr = addr.set_crs(4326, allow_override=True)
    
    # Consumer count and network parameters
    col1, col2 = st.columns(2)
    with col1:
        take_n = st.slider("Number of consumers to route to", min_value=10, max_value=min(500, len(addr_with_loads)), value=min(50, len(addr_with_loads)), step=10)
    with col2:
        dist_m = st.slider("Street network radius (m)", min_value=400, max_value=3000, value=1200, step=100)
    
    if st.button("🚀 Build OSM-routed pipes (demo)", type="primary"):
        with st.spinner("🌐 Downloading OSM street network and computing optimal routes..."):
            try:
                # Route pipes using OSM street network
                plant = (float(plant_lat), float(plant_lon))
                pipes_osm = route_pipes_from_osm(addr, plant_latlon=plant, take_n=take_n, dist_m=dist_m)
                
                st.success(f"✅ Routed {len(pipes_osm)} pipe segments along streets!")
                st.info(f"🏭 Plant location: {plant_lat:.3f}, {plant_lon:.3f}")
                st.info(f"🏠 Connected {take_n} consumers via street network")
                
                # Create map centered on plant
                m3 = folium.Map(location=[plant_lat, plant_lon], zoom_start=15, tiles="cartodbpositron")
                
                # Add plant marker
                folium.Marker(
                    location=[plant_lat, plant_lon],
                    popup="🏭 Heat Plant",
                    icon=folium.Icon(color="red", icon="industry", prefix="fa")
                ).add_to(m3)
                
                # Visualize the OSM-routed pipes
                gradient_layer(m3, pipes_osm, value="pressure", diameter_col="diameter_m")
                
                st_folium(m3, height=700, use_container_width=True)
                
                # Show network statistics
                with st.expander("📊 Network Statistics"):
                    total_length = pipes_osm['length_m'].sum()
                    avg_diameter = pipes_osm['diameter_m'].mean()
                    st.write(f"**Total pipe length:** {total_length:.0f} m ({total_length/1000:.1f} km)")
                    st.write(f"**Average diameter:** {avg_diameter:.3f} m")
                    st.write(f"**Number of pipe segments:** {len(pipes_osm)}")
                    st.write(f"**Network density:** {len(pipes_osm)/total_length*1000:.1f} segments/km")
                
                # Export functionality
                with st.expander("💾 Export OSM-Routed Network"):
                    st.write("Save the OSM-routed pipe network as a GeoJSON file for use in other applications.")
                    
                    # Create download button
                    geojson_str = pipes_osm.to_json()
                    st.download_button(
                        label="📁 Download as GeoJSON",
                        data=geojson_str,
                        file_name="osm_routed_pipes.geojson",
                        mime="application/geo+json",
                        help="Download the OSM-routed pipe network as a GeoJSON file"
                    )
                    
                    # Show preview of the data
                    st.write("**Data Preview:**")
                    st.dataframe(pipes_osm[['length_m', 'diameter_m']].head(10))
                    
                st.info("💡 **Next steps:** Use these OSM-routed pipes as input for pandapipes simulation in the Temperature tab!")
                
            except Exception as e:
                st.error(f"❌ OSM routing failed: {str(e)}")
                st.info("💡 **Troubleshooting:** Check internet connection and try reducing the radius/consumer count.")
    
    else:
        st.info("👆 Click the button above to generate a street-based pipe network!")
        st.write("**How it works:**")
        st.write("1. 🌐 Downloads OpenStreetMap street network around Branitz")
        st.write("2. 📍 Snaps consumers and plant to nearest street nodes")
        st.write("3. 🌳 Computes optimal Steiner tree connecting all points")
        st.write("4. 🗺️ Returns realistic pipe routes following streets")