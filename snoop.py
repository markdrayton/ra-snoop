#!/usr/bin/env python3

import argparse
import os
import scraper

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("-c", "--cache", default="~/.saved", metavar="DIR",
            type=lambda x: os.path.expanduser(x),
            help="cache dir (default %(default)s)")
    ap.add_argument("-n", "--dryrun", action="store_true")
    ap.add_argument("artists", nargs="+", metavar="artist")
    return ap.parse_args()

def cache_path(base, artist):
    return os.path.join(base, artist)

def read_cached(path):
    try:
        return open(path).read().splitlines()
    except FileNotFoundError:
        return []

def save(path, listing):
    f = open(path, "w")
    f.write("\n".join(listing))
    f.write("\n")
    f.close()

args = parse_args()
listings = {artist: scraper.scrape(artist) for artist in args.artists}

for artist in sorted(listings):
    path = cache_path(args.cache, artist)
    saved = set(read_cached(path))
    scraped = set(listings[artist])
    added = sorted(scraped - saved)
    removed = sorted(saved - scraped)
    if added or removed:
        print("==> {}".format(artist))
        print()
        for line in removed:
            print("-{}".format(line))
        for line in added:
            print("+{}".format(line))
        print()

if not args.dryrun:
    try:
        os.mkdir(args.cache)
    except OSError as e:
        if e.errno != 17:  # EEXIST
            raise
    for artist, listing in listings.items():
        path = cache_path(args.cache, artist)
        save(path, listing)
