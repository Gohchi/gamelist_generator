#!/usr/bin/env python3

import copy
import os
import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Supported ROM extensions
ROM_EXTENSIONS = {
    ".zip", ".7z",
    ".bin", ".md", ".gen", ".smd",
    ".nes", ".fds",
    ".gb", ".gbc", ".gba",
    ".sms", ".gg",
    ".pce",
    ".cue", ".iso", ".chd", ".pbp",
    ".n64", ".z64", ".v64",
    ".nds"
}

IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg"]

REMOVE_MISSING_ENTRIES = False


def _strip_empty_whitespace(elem):
    for child in elem.iter():
        if child.text is not None and child.text.strip() == "":
            child.text = None

        if child.tail is not None and child.tail.strip() == "":
            child.tail = None


def pretty_xml(root):
    _strip_empty_whitespace(root)
    xml = ET.tostring(root, encoding="utf-8")
    return minidom.parseString(xml).toprettyxml(indent="\t", encoding="utf-8")


def title_from_filename(filename):
    return os.path.splitext(filename)[0]


def find_image(images_folder, rom_filename):
    base = os.path.splitext(rom_filename)[0]

    for ext in IMAGE_EXTENSIONS:
        candidate = os.path.join(images_folder, base + ext)
        if os.path.exists(candidate):
            return "./images/" + base + ext

    return ""


def next_gameid(root):
    highest = 0

    for game in root.findall("game"):
        gid = game.findtext("gameid")

        if gid and gid.isdigit():
            highest = max(highest, int(gid))

    return highest + 1


def update_field(game, tag, value):
    node = game.find(tag)

    if node is None:
        node = ET.SubElement(game, tag)

    node.text = value


def main(folder):

    xml_path = os.path.join(folder, "gamelist.xml")
    images_folder = os.path.join(folder, "images")

    if not os.path.exists(xml_path):
        print("No gamelist.xml found.")
        return

    tree = ET.parse(xml_path)
    root = tree.getroot()

    template = root.find("game")

    if template is None:
        print("No template game found.")
        return

    existing = {}

    for game in root.findall("game"):
        path = game.findtext("path", "")
        existing[path] = game

    roms = []

    for file in sorted(os.listdir(folder)):
        if os.path.isdir(os.path.join(folder, file)):
            continue

        ext = os.path.splitext(file)[1].lower()

        if ext in ROM_EXTENSIONS:
            roms.append(file)

    if REMOVE_MISSING_ENTRIES:
        for game in list(root.findall("game")):
            path = game.findtext("path", "")

            if path.startswith("./"):
                filename = path[2:]

                if filename not in roms:
                    root.remove(game)

    gameid = next_gameid(root)

    added = 0

    for rom in roms:

        path = "./" + rom

        if path in existing:
            continue

        title = title_from_filename(rom)

        game = copy.deepcopy(template)

        update_field(game, "gameid", str(gameid))
        update_field(game, "path", path)
        update_field(game, "image", find_image(images_folder, rom))
        update_field(game, "en_US", title)
        update_field(game, "zh_CN", title)
        update_field(game, "zh_TW", title)
        update_field(game, "ko_KR", title)
        update_field(game, "name", title)

        root.append(game)

        gameid += 1
        added += 1

    with open(xml_path, "wb") as f:
        f.write(pretty_xml(root))

    print("------------------------------------")
    print("Folder :", folder)
    print("ROMs   :", len(roms))
    print("Added  :", added)
    print("Total  :", len(root.findall("game")))
    print("------------------------------------")


if __name__ == "__main__":

    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        path = os.getcwd()
        main(path)
