#!/usr/bin/python3

import io, urllib.request, time, re, random
import argparse
import os
import sys
import math
import gpxpy
import gpxpy.gpx
import shutil
import img2pdf
from PIL import Image, ImageDraw, ImageFont

TILE_SIZE_PX = 256

parser = argparse.ArgumentParser(description="Create printable PDF with OSM data corresponding to your GPX track.")
parser.add_argument("--tiles", type=str, default="outdoors", choices=["cycle", "transport",
                    "landscape", "outdoors", "transport-dark", "spinal-map", "pioneer",
                    "mobile-atlas", "neighbourhood"],
                    metavar="tiles_source", help="tiles source (default: outdoors)")
parser.add_argument("--zoom", type=int, default=14, metavar="zoom_level",
                    help="zoom level (default: 14)")
parser.add_argument("--pdf", type=str, default="map.pdf", metavar="pdf_name",
                    help="output pdf name (default: map.pdf)")
parser.add_argument("--gpx", type=str, required=True, metavar="gpx_file",
                    help="Your GPX route data")
parser.add_argument("--width", type=int, default=1792, metavar="output_image_width",
                    help="Width of the output image (default: 1792)")
parser.add_argument("--height", type=int, default=1280, metavar="output_image_height",
                    help="Height of the output image (default: 1280)")
parser.add_argument("--preserve-tmp", dest="preserve_tmp", action="store_true",
                    help="Prevents deletion of the tmp folder")
parser.add_argument("--no-pdf", dest="no_pdf", action="store_true",
                    help="Prevents pdf creation")
parser.add_argument("--api-key", type=str, metavar="api_key",
                    help="Thunderforest api key")
parser.add_argument("--no-labels", dest="no_labels", action="store_true",
                    help="Disables coordinate labels")
args = parser.parse_args()

APIkey = ""
if args.api_key:
    APIkey = args.api_key
else:
    APIkey = os.getenv("THUNDERFOREST_API_KEY")

layer = f"https://a.tile.thunderforest.com/{args.tiles}/!z/!x/!y.png?apikey={APIkey}"
api_counter = 0
chunk_counter = 1
os.mkdir("tmp/")
img_list = []

# deg2num & num2deg methods were stolen from here:
# https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Derivation_of_tile_names
def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)

# this returns the NW-corner of the square
def num2deg(xtile, ytile, zoom):
  n = 2.0 ** zoom
  lon_deg = xtile / n * 360.0 - 180.0
  lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
  lat_deg = math.degrees(lat_rad)
  return (lat_deg, lon_deg)

def round_to_tile_size(input_size):
    return TILE_SIZE_PX * round(input_size / TILE_SIZE_PX)

def draw_progress_bar(count, total, suffix):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = "=" * filled_len + " " * (bar_len - filled_len)

    sys.stdout.write('[%s] %s\r' % (bar, suffix))
    sys.stdout.flush()

# checks if the chunk with top left corner coordinates (x, y) containes
# any piece of the GPX track
def chunk_containes_track(x, y):
    corner1_lat, corner1_lon = num2deg(x, y, args.zoom)
    corner2_lat, corner2_lon = num2deg(x + output_width_tiles, y + output_height_tiles,\
                                         args.zoom)
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                if point.latitude >= min(corner1_lat, corner2_lat) and \
                   point.latitude <= max(corner1_lat, corner2_lat) and \
                   point.longitude >= min(corner1_lon, corner2_lon) and \
                   point.longitude <= max(corner1_lon, corner2_lon):
                    return True
    return False

# builds new output image
def process_chunk(x, y, xmin, ymin, xmax, ymax):
    global chunk_counter
    if not chunk_containes_track(x, y):
        print(f">>> Chunk {chunk_counter} contains no route pieces")
        return
    print(f">>> Chunk {chunk_counter} contains route piece")
    resultImage = Image.new("RGB", (output_width_px, output_height_px), (0,0,0))
    processing_status = 0
    amount_to_process = output_width_tiles * output_height_tiles
    for i in range(x, x + output_width_tiles):
        for j in range(y, y + output_height_tiles):
            url = layer.replace("!x", str(i)).replace("!y", str(j)).replace("!z", str(args.zoom))
            match = re.search("{([a-z0-9]+)}", url)
            if match:
                url = url.replace(match.group(0), random.choice(match.group(1)))
            try:
                req = urllib.request.Request(url)
                tile = urllib.request.urlopen(req).read()
            except Exception as e:
                print(f"Error: {e}")
                continue;
            image = Image.open(io.BytesIO(tile))
            tileImage = Image.new("RGBA", (TILE_SIZE_PX, TILE_SIZE_PX), (0,0,0,0))
            tileImage.paste(image, None, image.convert("RGBA"))
            alpha = tileImage.convert("RGBA").getchannel("A")
            resultImage.paste(image, ((i - x) * TILE_SIZE_PX, (j - y) * TILE_SIZE_PX), mask=alpha)
            processing_status = processing_status + 1 
            draw_progress_bar(processing_status, amount_to_process, "")
    font = ImageFont.truetype("raleway.ttf", 30)
    draw = ImageDraw.Draw(resultImage)
    if not args.no_labels:
        page_x = int((x - xmin) / output_width_tiles)
        page_y = int((y - ymin) / output_height_tiles)
        draw.text((20, 20), f"({page_x}, {page_y})", (127,127,127), font=font)
    resultImage.save(f"tmp/{chunk_counter}.png")
    if not args.no_pdf:
        img_list.append(f"tmp/{chunk_counter}.png")
    print("\n", end="")


output_width_px = round_to_tile_size(args.width)
output_height_px = round_to_tile_size(args.height)
output_width_tiles = int(output_width_px / TILE_SIZE_PX)
output_height_tiles = int(output_height_px / TILE_SIZE_PX)

gpx_file = open(f"{args.gpx}", "r")
gpx = gpxpy.parse(gpx_file)
if len(gpx.tracks) == 0:
    print("Error: no GPX track found in your .gpx file")

latmax = -90
latmin = 90
lonmax = -180
lonmin = 180
for track in gpx.tracks:
    for segment in track.segments:
        for point in segment.points:
            latmax = max(latmax, point.latitude)
            latmin = min(latmin, point.latitude)
            lonmax = max(lonmax, point.longitude)
            lonmin = min(lonmin, point.longitude)

# these coordinates are tiles numbers
tile1_x, tile1_y = deg2num(latmax, lonmax, args.zoom)
tile2_x, tile2_y = deg2num(latmin, lonmin, args.zoom)
ymax = max(tile1_y, tile2_y) + 1
ymin = min(tile1_y, tile2_y) - 1
xmax = max(tile1_x, tile2_x) + 1
xmin = min(tile1_x, tile2_x) - 1
xmax = xmax + math.ceil((xmax - xmin + 1) / output_width_tiles)\
       * output_width_tiles - (xmax - xmin + 1)
ymax = ymax + math.ceil((ymax - ymin + 1) / output_height_tiles)\
       * output_height_tiles - (ymax - ymin + 1)
xsize = int(xmax - xmin + 1)
ysize = int(ymax - ymin + 1)
print(f"Area size in tiles: {xsize} x {ysize}")
print(f"Print chunk in tiles: {output_width_tiles} x {output_height_tiles}")

x = xmin
y = ymin
total_chunks = (xsize * ysize) / (output_width_tiles * output_height_tiles)
while x <= xmax:
    while y <= ymax:
        process_chunk(x, y, xmin, ymin, xmax, ymax)
        progress = int(chunk_counter * 100 / total_chunks)
        print(f"{progress}%")
        chunk_counter = chunk_counter + 1
        y = y + output_height_tiles
    y = ymin
    x = x + output_width_tiles

if not args.no_pdf:
    print("Importing to PDF...")
    a4inpt = (img2pdf.mm_to_pt(297), img2pdf.mm_to_pt(210))
    borders = (img2pdf.mm_to_pt(5), img2pdf.mm_to_pt(2))
    layout_fun = img2pdf.get_layout_fun(pagesize=a4inpt, border=borders)
    with open(args.pdf, "wb") as f:
        f.write(img2pdf.convert(img_list, layout_fun=layout_fun))

if not args.preserve_tmp:
    shutil.rmtree("tmp/")
