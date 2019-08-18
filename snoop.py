#!/usr/bin/env python3

import argparse
import scraper

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--dryrun", action="store_true")
    ap.add_argument("artists", nargs="+", metavar="artist")
    return ap.parse_args()

def read_saved(artist):
    try:
        return open(".saved/{}".format(artist)).read().splitlines()
    except FileNotFoundError:
        return []

def save(artist, listing):
    f = open(".saved/{}".format(artist), "w")
    f.write("\n".join(listing))
    f.write("\n")
    f.close()

args = parse_args()
listings = {artist: scraper.scrape(artist) for artist in args.artists}

for artist in sorted(listings):
    saved = set(read_saved(artist))
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
    for artist, listing in listings.items():
        save(artist, listing)
