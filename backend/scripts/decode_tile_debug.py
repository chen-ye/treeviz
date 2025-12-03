import requests
import mapbox_vector_tile
import mercantile
from shapely.geometry import shape

# Seattle center
lat, lon, z = 47.6062, -122.3321, 14
# Compute tile coordinates
x, y = mercantile.tile(lon, lat, z).x, mercantile.tile(lon, lat, z).y

# Fetch TileJSON to get the correct template
tilejson_url = "https://tiles.openfreemap.org/planet"
r = requests.get(tilejson_url, timeout=10)
r.raise_for_status()
tj = r.json()
tpl = tj['tiles'][0]
url = tpl.format(z=z, x=x, y=y)
print(f"Fetching tile: {url}")
tr = requests.get(url, timeout=10)
tr.raise_for_status()
data = tr.content
print(f"Fetched {len(data)} bytes")

decoded = mapbox_vector_tile.decode(data)
print(f"Decoded layers: {list(decoded.keys())}")

# Print a sample feature from landuse, landcover, and building layers
for layer_name in ['landuse', 'landcover', 'building', 'park']:
    layer = decoded.get(layer_name)
    if not layer:
        print(f"Layer {layer_name} not present.")
        continue
    print(f"Layer {layer_name} has {len(layer)} features.")
    # Print first feature's geometry and properties
    print(f"Layer type: {type(layer)}")
    if isinstance(layer, dict):
        print(f"Layer keys: {layer.keys()}")
        if 'features' in layer:
            feat = layer['features'][0] if layer['features'] else None
        else:
            feat = None
    else:
        feat = layer[0] if layer else None
    if feat:
        print(f"Sample feature in {layer_name}:")
        print(f"  type: {feat.get('type')}")
        print(f"  properties: {feat.get('properties')}")
        print(f"  geometry: {feat.get('geometry')}")
        try:
            geom_shape = shape(feat.get('geometry'))
            print(f"  bounds: {geom_shape.bounds}")
        except Exception as e:
            print(f"  Could not build shapely geometry: {e}")
    break
