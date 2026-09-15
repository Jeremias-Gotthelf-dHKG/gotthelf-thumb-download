import argparse
import os
from pathlib import Path, PurePosixPath
from typing import TypedDict
from urllib.request import urlopen, Request, HTTPError
from urllib.parse import urlparse, urlunparse, unquote, quote
from hashlib import md5
from random import random
import xml.etree.ElementTree as ET
import time
from wand.image import Image

parser = argparse.ArgumentParser()
parser.add_argument("url", help="URL to download images XML from")
parser.add_argument("dest", help="Destination folder to download images to")
parser.add_argument("-f", "--force", help="Force redownload even if images already exist", action='store_true')

args = parser.parse_args()
dest = Path(args.dest)

if not (dest.is_dir() and os.access(dest, os.W_OK)):
    print(f"Destination path '{dest}' not writable or not a directory")
    exit(1)

class ImageRecord(TypedDict):
    path: Path
    url: str

images: list[ImageRecord] = []
subpaths: set[Path] = set()

with urlopen(args.url) as xml_file:
    xml_tree = ET.parse(xml_file)
    xml_root = xml_tree.getroot()

    for xml_img in xml_root.findall(".//img"):
        images.append({ "path": dest / xml_img.findtext("file"), "url": xml_img.findtext("url")})
        subpaths.add((dest / xml_img.findtext("file")).parent)

to_download = [img for img in images if not img["path"].is_file()]

print(f"Discovered {len(images)} images in XML input, {len(to_download)} are missing")

if args.force:
    print("Forcing download of all images")
    to_download = images

print(f"{len(to_download)} images to download")

for path in subpaths:
    path.mkdir(parents=True, exist_ok=True)

RETRIES = 0
MAX_RETRIES = 5

for img in to_download:
    tmp_path = img["path"].parent / (img["path"].name + ".tmp")
    #print(f"Downloading {img['url']}")
    while RETRIES < MAX_RETRIES:
        try:
            with open(tmp_path, "wb") as output_file:
                url = urlparse(img["url"])
                if url.netloc == "commons.wikimedia.org":
                    filename = unquote(PurePosixPath(url.path).name).replace(" ", "_")
                    filename_hash = md5(filename.encode()).hexdigest()
                    filename = quote(filename)
                    new_path = "/wikipedia/commons/" + filename_hash[:1] + "/" + filename_hash[:2] + "/" + filename
                    url = url._replace(netloc="upload.wikimedia.org")._replace(path=new_path)._replace(query="")
                    img["url"] = urlunparse(url)
                with urlopen(Request(img["url"], headers={'User-Agent': 'GotthelfThumbnails/1.0'})) as image_file:
                    if url.netloc == "commons.wikimedia.org":
                        with Image(file=image_file) as image:
                            ratio = image.width / 200
                            image.resize(200, round(image.height / ratio))
                            image.save(file=output_file)
                    else:
                        output_file.write(image_file.read())

            tmp_path.replace(img["path"])
            print(f"Downloaded {img['url']} as {img['path']}")
            break
        except HTTPError as e:
            if e.code == 404:
                print(f"Image not found (404): {img['url']}")
                break
            RETRIES += 1
            print(f"Error downloading {img['url']}: {e}. Retry {RETRIES}/{MAX_RETRIES}")
        time.sleep(5 * 2 ** (RETRIES - 1))

    time.sleep(1 + random())
