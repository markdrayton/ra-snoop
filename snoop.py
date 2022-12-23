#!/usr/bin/env python3

import aiohttp
import argparse
import asyncio
import datetime
import json
import os
import sys
from collections import defaultdict
from collections import namedtuple

from parser import parse_events


Event = namedtuple("Event", "date name address")
Change = namedtuple("Change", "symbol event")


UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:106.0) Gecko/20100101 Firefox/106.0"


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "-c",
        "--cache",
        default="~/.ra-snoop.json",
        metavar="PATH",
        type=lambda x: os.path.expanduser(x),
        help="cache dir (default %(default)s)",
    )
    ap.add_argument("-n", "--dryrun", action="store_true")
    ap.add_argument("artists", nargs="+", metavar="artist")
    return ap.parse_args()


def read_cached(path):
    try:
        return {
            artist: [Event(*event) for event in events]
            for artist, events in json.load(open(path)).items()
        }
    except FileNotFoundError:
        return {}


def save(path, listings):
    with open(path, "w") as f:
        json.dump(listings, f)


def url(artist):
    return f"https://ra.co/dj/{artist}/tour-dates"


async def fetch_listing(session, artist):
    resp = await session.request(method="GET", url=url(artist))
    resp.raise_for_status()
    html = await resp.text()
    return [Event(*event) for event in parse_events(html)]


async def fetch_listings(artists):
    async with aiohttp.ClientSession(headers={"User-Agent": UA}) as session:
        tasks = []
        for artist in artists:
            tasks.append(fetch_listing(session, artist))
        return await asyncio.gather(*tasks)


async def main():
    args = parse_args()
    artists = sorted(args.artists)
    listings = await fetch_listings(artists)
    cache = read_cached(args.cache)

    output = defaultdict(list)

    for artist, listing in zip(artists, listings):
        saved = set(cache.get(artist, []))
        scraped = set(listing)
        for event in sorted(scraped - saved):
            output[artist].append(Change("+", event))
        for event in sorted(saved - scraped):
            output[artist].append(Change("-", event))

    if output:
        namewidth = max(
            len(change.event.name) for changes in output.values() for change in changes
        )

        for artist, changes in sorted(output.items()):
            print(f"==> {artist}")
            print()
            for symbol, event in sorted(changes, key=lambda c: c.event.date):
                print(
                    f"{symbol}{event.date}  {event.name:{namewidth}}  {event.address}"
                )
            print()

        if not args.dryrun:
            save(args.cache, dict(zip(artists, listings)))


asyncio.run(main())
