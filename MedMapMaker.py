import rasterio
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
from matplotlib.colors import ListedColormap, LogNorm
import json

def parse_point(pointstring):
    halves = pointstring.split(',')
    x = float(halves[0].lstrip('Point(')) # longitude 
    y = float(halves[1].rstrip(')')) # latitude
    point = Point(x,y)
    return point

ports = {
    name: parse_point(pt_str)
    for name, pt_str in config['ports'].items()
}
filepath = r'./popd_2025AD_med.tif'

with rasterio.open(filepath) as src:
    nodata = src.nodata
    data = src.read(1)
    bounds = src.bounds
    extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]

water_color = "#06133A"
land_color  = "#FFFFCC"

FIG_W_IN, FIG_H_IN, DPI = 16, 8, 500

# ---------- LAYER 1: background only (water, land, population) ----------
fig, ax = plt.subplots(figsize=(FIG_W_IN, FIG_H_IN), facecolor=water_color)
ax.set_position([0, 0, 1, 1])  # no margins -> pixel grid maps linearly to bounds
ax.set_facecolor(water_color)

land_zero_masked = np.ma.masked_where(data != 0, data)
cmap_land = ListedColormap([land_color])
ax.imshow(land_zero_masked, extent=extent, origin='upper', cmap=cmap_land,
          aspect='auto', interpolation='nearest', zorder=1)

masked_log = np.ma.masked_where(data <= 0, data)
cmap_pop = matplotlib.colormaps['YlOrRd'].copy()
cmap_pop.set_bad(color='none')
norm = LogNorm(vmin=0.1, vmax=100_000)
ax.imshow(masked_log, extent=extent, origin='upper', cmap=cmap_pop, norm=norm,
          aspect='auto', interpolation='nearest', zorder=2)

ax.set_xlim(bounds.left, bounds.right)
ax.set_ylim(bounds.bottom, bounds.top)
ax.axis('off')

plt.savefig('assets/map_background.png', dpi=DPI, facecolor=fig.get_facecolor())
plt.close(fig)

# ---------- LAYER 2: dots + labels only, transparent background ----------
fig, ax = plt.subplots(figsize=(FIG_W_IN, FIG_H_IN))
ax.set_position([0, 0, 1, 1])
ax.set_xlim(bounds.left, bounds.right)
ax.set_ylim(bounds.bottom, bounds.top)
ax.axis('off')
ax.patch.set_alpha(0)  # transparent axes background

points_to_plot = [{"name": name, "x": pt.x, "y": pt.y} for name, pt in ports.items()]
xs = [p["x"] for p in points_to_plot]
ys = [p["y"] for p in points_to_plot]

ax.scatter(xs, ys, color="#bbfcc8", edgecolor='#ffffff', s=35, zorder=3)

for p in points_to_plot:
    ann = ax.annotate(
        p["name"], xy=(p["x"], p["y"]), xytext=(6, 4),
        textcoords='offset points', color='#ffffff',
        fontsize=12, fontweight='bold', zorder=4
    )
    ann.set_path_effects([path_effects.withStroke(linewidth=2, foreground='#080808')])

plt.savefig('assets/map_overlay.png', dpi=DPI, transparent=True)
plt.close(fig)

# ---------- Persist pixel <-> geo mapping for the game to use ----------
img_w, img_h = int(FIG_W_IN * DPI), int(FIG_H_IN * DPI)
with open('assets/map_bounds.json', 'w') as f:
    json.dump({
        "left": bounds.left, "right": bounds.right,
        "bottom": bounds.bottom, "top": bounds.top,
        "img_w": img_w, "img_h": img_h
    }, f)

print("Saved map_background.png, map_overlay.png, map_bounds.json")