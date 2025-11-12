"""
Visualization utilities for the DH project.
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import pandas as pd
import folium
from branca.colormap import linear
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
import logging

from .config import Config
from .data_adapters import DataAdapter


class Visualizer:
    """Visualization manager for creating plots and charts."""
    
    def __init__(self, config: Config):
        """Initialize visualizer.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.data_adapter = DataAdapter(config)
        self.logger = logging.getLogger(__name__)
        
        # Set up plotting style
        self._setup_style()
    
    def _setup_style(self):
        """Set up matplotlib and seaborn styling."""
        style = self.config.get("visualization.default_style", "seaborn-v0_8")
        try:
            plt.style.use(style)
        except OSError:
            self.logger.warning(f"Style '{style}' not found, using default")
            plt.style.use('default')
        
        # Set default figure size
        fig_size = self.config.get("visualization.figure_size", [12, 8])
        plt.rcParams['figure.figsize'] = fig_size
    
    def plot_timeline(self, data: pd.DataFrame, date_col: str, 
                     value_col: str, title: str = "Timeline", 
                     save_path: Optional[str] = None) -> plt.Figure:
        """Create a timeline plot.
        
        Args:
            data: DataFrame with timeline data
            date_col: Column name containing dates
            value_col: Column name containing values
            title: Plot title
            save_path: Optional path to save the plot
            
        Returns:
            Matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=self.config.get("visualization.figure_size", [12, 8]))
        
        # Convert date column if needed
        if not pd.api.types.is_datetime64_any_dtype(data[date_col]):
            data[date_col] = pd.to_datetime(data[date_col])
        
        ax.plot(data[date_col], data[value_col], linewidth=2)
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_xlabel(date_col, fontsize=12)
        ax.set_ylabel(value_col, fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # Rotate x-axis labels if needed
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        if save_path:
            self._save_plot(fig, save_path)
        
        return fig
    
    def plot_distribution(self, data: pd.Series, title: str = "Distribution",
                         bins: int = 30, save_path: Optional[str] = None) -> plt.Figure:
        """Create a distribution plot.
        
        Args:
            data: Data series to plot
            title: Plot title
            bins: Number of histogram bins
            save_path: Optional path to save the plot
            
        Returns:
            Matplotlib figure object
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # Histogram
        ax1.hist(data.dropna(), bins=bins, alpha=0.7, color='skyblue', edgecolor='black')
        ax1.set_title(f'{title} - Histogram', fontweight='bold')
        ax1.set_xlabel(data.name or 'Value')
        ax1.set_ylabel('Frequency')
        ax1.grid(True, alpha=0.3)
        
        # Box plot
        ax2.boxplot(data.dropna())
        ax2.set_title(f'{title} - Box Plot', fontweight='bold')
        ax2.set_ylabel(data.name or 'Value')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            self._save_plot(fig, save_path)
        
        return fig
    
    def plot_correlation_heatmap(self, data: pd.DataFrame, title: str = "Correlation Matrix",
                                save_path: Optional[str] = None) -> plt.Figure:
        """Create a correlation heatmap.
        
        Args:
            data: DataFrame with numeric columns
            title: Plot title
            save_path: Optional path to save the plot
            
        Returns:
            Matplotlib figure object
        """
        # Calculate correlation matrix
        numeric_data = data.select_dtypes(include=[np.number])
        corr_matrix = numeric_data.corr()
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Create heatmap
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
        sns.heatmap(corr_matrix, mask=mask, annot=True, cmap='coolwarm', center=0,
                   square=True, linewidths=0.5, cbar_kws={"shrink": 0.8})
        
        ax.set_title(title, fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            self._save_plot(fig, save_path)
        
        return fig
    
    def plot_word_cloud(self, text_data: Union[str, List[str]], title: str = "Word Cloud",
                       save_path: Optional[str] = None) -> plt.Figure:
        """Create a word cloud visualization.
        
        Args:
            text_data: Text data (string or list of strings)
            title: Plot title
            save_path: Optional path to save the plot
            
        Returns:
            Matplotlib figure object
        """
        try:
            from wordcloud import WordCloud
        except ImportError:
            self.logger.error("WordCloud library not installed. Install with: pip install wordcloud")
            raise ImportError("WordCloud library is required for word cloud visualization")
        
        # Prepare text data
        if isinstance(text_data, list):
            text = ' '.join(text_data)
        else:
            text = text_data
        
        # Generate word cloud
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
        
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        ax.set_title(title, fontsize=16, fontweight='bold')
        
        if save_path:
            self._save_plot(fig, save_path)
        
        return fig
    
    def plot_network(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]], 
                    title: str = "Network Graph", save_path: Optional[str] = None) -> plt.Figure:
        """Create a network visualization.
        
        Args:
            nodes: List of node dictionaries with 'id', 'label', etc.
            edges: List of edge dictionaries with 'source', 'target', etc.
            title: Plot title
            save_path: Optional path to save the plot
            
        Returns:
            Matplotlib figure object
        """
        try:
            import networkx as nx
        except ImportError:
            self.logger.error("NetworkX library not installed. Install with: pip install networkx")
            raise ImportError("NetworkX library is required for network visualization")
        
        # Create graph
        G = nx.Graph()
        
        # Add nodes
        for node in nodes:
            G.add_node(node['id'], **{k: v for k, v in node.items() if k != 'id'})
        
        # Add edges
        for edge in edges:
            G.add_edge(edge['source'], edge['target'], 
                      **{k: v for k, v in edge.items() if k not in ['source', 'target']})
        
        # Create layout
        pos = nx.spring_layout(G, k=1, iterations=50)
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Draw network
        nx.draw_networkx_nodes(G, pos, node_color='lightblue', node_size=500, ax=ax)
        nx.draw_networkx_edges(G, pos, alpha=0.5, ax=ax)
        nx.draw_networkx_labels(G, pos, ax=ax)
        
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.axis('off')
        
        if save_path:
            self._save_plot(fig, save_path)
        
        return fig
    
    def create_dashboard(self, plots: List[plt.Figure], title: str = "Dashboard",
                        save_path: Optional[str] = None) -> plt.Figure:
        """Create a dashboard with multiple plots.
        
        Args:
            plots: List of matplotlib figures
            title: Dashboard title
            save_path: Optional path to save the dashboard
            
        Returns:
            Combined figure object
        """
        n_plots = len(plots)
        cols = min(3, n_plots)
        rows = (n_plots + cols - 1) // cols
        
        fig, axes = plt.subplots(rows, cols, figsize=(5*cols, 4*rows))
        if rows == 1 and cols == 1:
            axes = [axes]
        elif rows == 1 or cols == 1:
            axes = axes.flatten()
        else:
            axes = axes.flatten()
        
        # Add title
        fig.suptitle(title, fontsize=20, fontweight='bold')
        
        # Hide unused subplots
        for i in range(n_plots, len(axes)):
            axes[i].axis('off')
        
        plt.tight_layout()
        
        if save_path:
            self._save_plot(fig, save_path)
        
        return fig
    
    def _save_plot(self, fig: plt.Figure, save_path: str):
        """Save plot to file.
        
        Args:
            fig: Matplotlib figure
            save_path: Path to save the plot
        """
        save_format = self.config.get("visualization.save_format", "png")
        full_path = self.data_adapter.data_dirs["outputs"] / f"{save_path}.{save_format}"
        
        fig.savefig(full_path, dpi=300, bbox_inches='tight')
        self.logger.info(f"Saved plot: {full_path}")
    
    def show_plot(self, fig: plt.Figure):
        """Display the plot.
        
        Args:
            fig: Matplotlib figure to display
        """
        plt.show()


def _finite_series(s):
    s = pd.to_numeric(s, errors="coerce")
    finite_mask = np.isfinite(s)
    return s[finite_mask]

def _length_m(geom) -> float:
    """Calculate length of geometry in meters by projecting to EPSG:25833."""
    import geopandas as gpd
    g = gpd.GeoSeries([geom], crs="EPSG:4326").to_crs(25833)
    return float(g.length.iloc[0])

def _offset_line(line, meters: float, crs_src="EPSG:4326", crs_m=25833):
    """Create a lateral offset of a line geometry."""
    import geopandas as gpd
    gs = gpd.GeoSeries([line], crs=crs_src).to_crs(crs_m)
    # offset perpendicular by translating small normal vector segment-wise
    # simple approx: translate x by meters, y by 0
    gs_off = gs.translate(xoff=meters, yoff=0.0)
    return gpd.GeoSeries(gs_off, crs=crs_m).to_crs(crs_src).iloc[0]

def width_px_from_diameter(d_m: float, dmin=0.05, dmax=0.30, px_min=2, px_max=10) -> float:
    """Map physical diameter (m) to a sane on-screen width (px), clamped."""
    import numpy as np
    if d_m is None or not np.isfinite(d_m):
        return px_min
    d = float(np.clip(d_m, dmin, dmax))
    return px_min + (px_max - px_min) * (d - dmin) / (dmax - dmin)

def paint_supply_return(map_obj, pipes_wgs, res_pipe, diameter_col="diameter_m",
                        temp=True, offset_m=0.6):
    """
    Draws two layers: supply (from) and return (to) with slight lateral offset.
    temp=True -> color by temperature; else by pressure.
    """
    if temp:
        cmap_s = linear.OrRd_09.scale(float(res_pipe["t_from_k"].min()), float(res_pipe["t_from_k"].max()))
        cmap_r = linear.OrRd_09.scale(float(res_pipe["t_to_k"].min()),   float(res_pipe["t_to_k"].max()))
        v_from, v_to = "t_from_k", "t_to_k"
    else:
        cmap_s = linear.Blues_09.scale(float(res_pipe["p_from_bar"].min()), float(res_pipe["p_from_bar"].max()))
        cmap_r = linear.Blues_09.scale(float(res_pipe["p_to_bar"].min()),   float(res_pipe["p_to_bar"].max()))
        v_from, v_to = "p_from_bar", "p_to_bar"

    for (i, r), idx in zip(pipes_wgs.iterrows(), res_pipe.index):
        line = r.geometry
        if line is None or len(line.coords) < 2: continue
        if _length_m(line) < 0.2: continue
        width = width_px_from_diameter(r.get(diameter_col, 0.08))

        # supply (offset +)
        ls = _offset_line(line, +offset_m)
        folium.PolyLine([(y,x) for x,y in ls.coords],
                        weight=width, color=cmap_s(float(res_pipe.loc[idx, v_from])), opacity=0.95).add_to(map_obj)
        # return (offset -)
        lr = _offset_line(line, -offset_m)
        folium.PolyLine([(y,x) for x,y in lr.coords],
                        weight=width, color=cmap_r(float(res_pipe.loc[idx, v_to])), opacity=0.95).add_to(map_obj)

    map_obj.add_child(cmap_s); map_obj.add_child(cmap_r)
    return map_obj

def gradient_layer(map_obj, pipes_gdf, value="pressure", diameter_col="diameter_m",
                   temp_range=None, press_range=None):
    """
    Colors each pipe with a gradient and line width by diameter.
    Pixel widths are small & clamped; handles None/NaN gracefully; skips tiny segments.
    """
    import pandas as pd
    if pipes_gdf.empty or pipes_gdf.geometry.isna().all():
        return map_obj

    # choose columns and limits
    if value == "pressure":
        if {"p_from","p_to"}.issubset(pipes_gdf.columns):
            v_from_all = _finite_series(pipes_gdf["p_from"])
            v_to_all   = _finite_series(pipes_gdf["p_to"])
            get_from = lambda r: r.get("p_from", None)
            get_to   = lambda r: r.get("p_to",   None)
        elif {"pressure_from","pressure_to"}.issubset(pipes_gdf.columns):
            v_from_all = _finite_series(pipes_gdf["pressure_from"])
            v_to_all   = _finite_series(pipes_gdf["pressure_to"])
            get_from = lambda r: r.get("pressure_from", None)
            get_to   = lambda r: r.get("pressure_to",   None)
        else:
            # neutral fallback so we at least draw geometry
            from branca.colormap import linear
            cmap = linear.Blues_09.scale(0.0, 1.0)
            get_from = lambda r: 0.5
            get_to   = lambda r: 0.5
            vmin, vmax = 0.0, 1.0
    else:
        # placeholder temperature limits for non-solved layer
        from branca.colormap import linear
        vmin, vmax = (temp_range or (318.0, 353.0))
        cmap = linear.OrRd_09.scale(vmin, vmax)
        get_from = lambda r: vmax
        get_to   = lambda r: vmin

    # build colormap for pressure (if not already set)
    if value == "pressure":
        from branca.colormap import linear
        allv = pd.concat([v_from_all, v_to_all], ignore_index=True)
        if len(allv) == 0:
            # No valid data, use neutral fallback
            vmin, vmax = 0.0, 1.0
        else:
            if press_range:
                vmin, vmax = float(press_range[0]), float(press_range[1])
            else:
                vmin = float(np.nanpercentile(allv, 1))
                vmax = float(np.nanpercentile(allv, 99))
            if not np.isfinite(vmin) or not np.isfinite(vmax) or vmin == vmax:
                vmin, vmax = float(allv.min()), float(allv.max() + 1e-6)
            if vmax < vmin:
                vmin, vmax = vmax, vmin
        # Ensure thresholds are valid for colormap
        if not np.isfinite(vmin) or not np.isfinite(vmax) or vmin >= vmax:
            vmin, vmax = 0.0, 1.0
        cmap = linear.Blues_09.scale(vmin, vmax)

    # draw
    for _, row in pipes_gdf.iterrows():
        line = row.geometry
        if line is None or len(line.coords) < 2:
            continue
        if _length_m(line) < 0.2:  # skip near-zero segments
            continue

        segs = list(zip(line.coords[:-1], line.coords[1:]))

        # None/NaN-safe conversions
        v0 = get_from(row);  v1 = get_to(row)
        v0 = np.nan if v0 is None else v0
        v1 = np.nan if v1 is None else v1
        v0 = float(pd.to_numeric(pd.Series([v0]), errors="coerce").iloc[0])
        v1 = float(pd.to_numeric(pd.Series([v1]), errors="coerce").iloc[0])
        if not np.isfinite(v0) or not np.isfinite(v1):
            continue

        vals = np.linspace(max(v0, vmin), min(v1, vmax), num=len(segs)+1)
        width = width_px_from_diameter(row.get(diameter_col, 0.08))

        for k, (a, b) in enumerate(segs):
            folium.PolyLine([(a[1], a[0]), (b[1], b[0])],
                            weight=width, color=cmap(float(vals[k])), opacity=0.95).add_to(map_obj)

    cmap.caption = "Pressure" if value == "pressure" else "Temperature (K)"
    map_obj.add_child(cmap)
    return map_obj



def repaint_with_results(map_obj, pipes_wgs, res_pipe, layer="temperature",
                         temp_range=None, press_range=None,
                         diameter_col="diameter_m"):
    """
    Repaint with pandapipes results (T or p). Width is diameter→px, no big multipliers.
    Safe if some results are missing.
    """
    from branca.colormap import linear
    # choose value arrays + colormap
    if layer == "temperature" and {"t_from_k","t_to_k"} <= set(res_pipe.columns):
        t0, t1 = res_pipe["t_from_k"], res_pipe["t_to_k"]
        if len(t0.dropna()) and len(t1.dropna()):
            vmin = temp_range[0] if temp_range else float(np.nanmin([t0.min(), t1.min()]))
            vmax = temp_range[1] if temp_range else float(np.nanmax([t0.max(), t1.max()]))
            cmap = linear.OrRd_09.scale(vmin, vmax)
            v_from, v_to = t0, t1
        else:
            layer = "pressure"

    if layer != "temperature":
        if {"p_from_bar","p_to_bar"} <= set(res_pipe.columns):
            p0, p1 = res_pipe["p_from_bar"], res_pipe["p_to_bar"]
            vmin = press_range[0] if press_range else float(np.nanmin([p0.min(), p1.min()]))
            vmax = press_range[1] if press_range else float(np.nanmax([p0.max(), p1.max()]))
            cmap = linear.Blues_09.scale(vmin, vmax)
            v_from, v_to = p0, p1
        else:
            # fall back to JSON pressure painter
            return gradient_layer(map_obj, pipes_wgs, value="pressure", diameter_col=diameter_col)

    # draw lines
    for (i, r), idx in zip(pipes_wgs.iterrows(), res_pipe.index):
        line = r.geometry
        if line is None or len(line.coords) < 2:
            continue
        if _length_m(line) < 0.2:
            continue

        coords = list(line.coords)
        segs = list(zip(coords[:-1], coords[1:]))

        try:
            vstart = float(v_from.loc[idx]); vend = float(v_to.loc[idx])
        except Exception:
            continue
        vals = np.linspace(vstart, vend, num=len(segs)+1)
        width = width_px_from_diameter(r.get(diameter_col, 0.08))

        for k, (a, b) in enumerate(segs):
            folium.PolyLine([(a[1], a[0]), (b[1], b[0])],
                            weight=width, color=cmap(float(vals[k])), opacity=0.95).add_to(map_obj)

    cmap.caption = "Temperature (K)" if layer == "temperature" else "Pressure (bar)"
    map_obj.add_child(cmap)
    return map_obj
