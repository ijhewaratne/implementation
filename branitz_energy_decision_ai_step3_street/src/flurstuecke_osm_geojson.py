import osmium
import shapely.wkb as wkblib
import geopandas as gpd

class BuildingHandler(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.buildings = []
        self.wkb_factory = osmium.geom.WKBFactory()

    def way(self, w):
        if 'building' in w.tags and w.tags['building'] != 'no':
            try:
                wkb = self.wkb_factory.create_multipolygon(w)
                geom = wkblib.loads(wkb, hex=True)
                props = dict(w.tags)
                props['osmid'] = w.id
                self.buildings.append({'geometry': geom, **props})
            except Exception:
                pass

def extract_building_geoms_osmium(osm_file, output_geojson=None, id_field="osmid"):
    handler = BuildingHandler()
    handler.apply_file(osm_file)
    gdf = gpd.GeoDataFrame(handler.buildings)
    if id_field not in gdf.columns:
        gdf[id_field] = gdf.index.astype(str)
    if output_geojson:
        gdf.to_file(output_geojson, driver="GeoJSON")
    return gdf

