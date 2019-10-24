#!/usr/bin/python3

import io, urllib.request, time, re, random
import argparse
import os
import math

from PIL import Image, ImageDraw


parser = argparse.ArgumentParser(description="Create a PNG file from OSM data.")
parser.add_argument("--tiles", type=str, default="outdoors", choices=["cycle", "transport",
                    "landscape", "outdoors", "transport-dark", "spinal-map", "pioneer",
                    "mobile-atlas", "neighbourhood"],
                    metavar="tiles_source", help="tiles source (default: outdoors)")
parser.add_argument("--zoom", type=int, default=14, metavar="zoom_level",
                    help="zoom level (default: 14)")
parser.add_argument("--out", type=str, default="output.png", metavar="output_name",
                    help="output file name (default: output.png)")
parser.add_argument("--laleft", type=float, required=True, metavar="latitude_left",
                    help="Latitude of the top left corner of the selected area")
parser.add_argument("--loleft", type=float, required=True, metavar="longitude_left",
                    help="Longitude of the top left corner of the selected area")
parser.add_argument("--laright", type=float, required=True, metavar="latitude_right",
                    help="Latitude of the bottom right corner of the selected area")
parser.add_argument("--loright", type=float, required=True, metavar="longitude_right",
                    help="Longitude of the bottom right corner of the selected area")
args = parser.parse_args()

# this method was stolen from here: https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Derivation_of_tile_names
def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)

APIkey = os.getenv("THUNDERFOREST_API_KEY")
layers = [f"https://a.tile.thunderforest.com/{args.tiles}/!z/!x/!y.png?apikey={APIkey}",
          f"https://b.tile.thunderforest.com/{args.tiles}/!z/!x/!y.png?apikey={APIkey}",
          f"https://c.tile.thunderforest.com/{args.tiles}/!z/!x/!y.png?apikey={APIkey}"]

# these coordinates are tiles numbers
xleft, yleft = deg2num(args.laleft, args.loleft, args.zoom)
xright, yright = deg2num(args.laright, args.loright, args.zoom)
ymax = max(yleft, yright)
ymin = min(yleft, yright)

xsize = xright - xleft + 1
ysize = ymax - ymin + 1

resultImage = Image.new("RGBA", (xsize * 256, ysize * 256), (0,0,0,0))

counter = 0
for x in range(xleft, xright + 1):
    for y in range(ymin, ymax + 1):
        for layer in layers:
            print(f"{x}, {y}, {layer}")
            url = layer.replace("!x", str(x)).replace("!y", str(y)).replace("!z", str(args.zoom))
            match = re.search("{([a-z0-9]+)}", url)
            if match:
                url = url.replace(match.group(0), random.choice(match.group(1)))
            print(f"{url} ...")
            try:
                req = urllib.request.Request(url)
                tile = urllib.request.urlopen(req).read()
            except Exception as e:
                print(f"Error: {e}")
                continue;
            image = Image.open(io.BytesIO(tile))
            resultImage.paste(image, ((x - xleft) * 256, (y - ymin) * 256), image.convert("RGBA"))
            counter += 1
            if counter == 10:
                time.sleep(2);
                counter = 0

draw = ImageDraw.Draw(resultImage)
del draw

resultImage.save(args.out)
