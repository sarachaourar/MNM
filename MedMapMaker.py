import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm, ListedColormap
import rasterio
import yaml
from shapely import Point

with open('config.yml', 'r') as f:
    config = yaml.safe_load(f)

def parse_point(pointstring):
    halves = pointstring.split(',')
    x = float(halves[0].lstrip('Point(')) # longitude 
    y = float(halves[1].rstrip(')')) # latitude
    return Point(x, y)

ports = {
    name: parse_point(pt_str) 
    for name, pt_str in config['ports'].items()
}

filepath = r'./popd_2025AD_med.tif'

# --- Open the raster and read everything ---
with rasterio.open(filepath) as src:
    nodata = src.nodata
    data = src.read(1)          # full band
    bounds = src.bounds         # left, bottom, right, top
    extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]

# --- Figure Setup ---
# 1. Define distinct colors for Water and Uninhabited Land
water_color = "#06133A"  # Deep water blue (or '#0d1117' for dark mode)
land_color  = "#FFFFCC"  # Dark gray for 0-population land

fig, ax = plt.subplots(figsize=(16, 8), facecolor=water_color)

# Water: Setting the axes background handles all -9999 (NoData) areas automatically
ax.set_facecolor(water_color)

# --- Layer 1: Plot Uninhabited Land (0 Values) ---
land_zero_masked = np.ma.masked_where(data != 0, data)
cmap_land = ListedColormap([land_color])

ax.imshow(
    land_zero_masked,
    extent=extent,
    origin='upper',
    cmap=cmap_land,
    aspect='auto',
    interpolation='nearest',
    zorder=1
)

# --- Layer 2: Plot Population Data (> 0 Values) ---
masked_log = np.ma.masked_where(data <= 0, data)

cmap_pop = matplotlib.colormaps['YlOrRd'].copy()
# Set bad values to transparent so lower land/water layers show through
cmap_pop.set_bad(color='none') 

norm = LogNorm(vmin=0.1, vmax=100_000)

im = ax.imshow(
    masked_log,
    extent=extent,
    origin='upper',
    cmap=cmap_pop,
    norm=norm,
    aspect='auto',
    interpolation='nearest',
    zorder=2
)

# --- Plot Points & Formatting ---
points_to_plot = [
    {"name": name, "x": pt.x, "y": pt.y}
    for name, pt in ports.items()
]

xs = [p["x"] for p in points_to_plot]
ys = [p["y"] for p in points_to_plot]

# Draw dots
ax.scatter(xs, ys, color="#bbfcc8", edgecolor='#ffffff', s=35, zorder=3)

# Draw labels
import matplotlib.patheffects as path_effects

# ... inside your function/loop ...

for p in points_to_plot:
    ann = ax.annotate(
        p["name"],
        xy=(p["x"], p["y"]),
        xytext=(6, 4),
        textcoords='offset points',
        color='#ffffff',
        fontsize=9,
        fontweight='bold',
        zorder=4
    )
    # Add a 2px dark outline around the text
    ann.set_path_effects([
        path_effects.withStroke(linewidth=2, foreground='#080808')
    ])

ax.set_xlim(bounds.left, bounds.right)
ax.set_ylim(bounds.bottom, bounds.top)

ax.axis('off')

plt.savefig(
    'assets/map.png', 
    dpi=500,
    bbox_inches='tight', 
    pad_inches=0, 
    facecolor=fig.get_facecolor()
)
print("Saved map.png")