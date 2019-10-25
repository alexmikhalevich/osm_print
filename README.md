# Printing OSM Maps

This repo contains the script to download OSM tiles and merge them into one map. You can find more information in my [blog](https://mikhalevich.com/2019/10/25/printing-osm-maps-v2/).

## Script usage

Here are the available script options:
- `--tiles`: specify the tiles source. Available sources: `cycle`, `transport`, `landscape`, `outdoors`, `transport-dark`, `spinal-map`, `pioneer`, `mobile-atlas`, `neighbourhood`. `Outdoors` is used by default.
- `--zoom`: the desired zoom level (14 by default).
- `--pdf`: name of the output PDF file (`map.pdf` by default).
- `--gpx`: path to the GPX track to print.
- `--width`: width of the output image in pixels (1792 by default).
- `--height`: height of the output image in pixels (1280 by default).
- `--preserve-tmp`: preserves the `tmp` folder which contains all the map chunks in PNG format.
- `--no-pdf`: do not merge PNG chunks into one PDF file. Can be useful in case of large maps.
- `--api-key`: Thunderforest API key. If no key provided, the `THUNDERFOREST_API_KEY` environmental variable will be used.
- `--no-labels`: prevent printing coordinate labels on the map.
