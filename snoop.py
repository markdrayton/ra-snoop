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
from functools import total_ordering

import arrow

from parser import parse_events


Change = namedtuple("Change", "symbol event")


UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:106.0) Gecko/20100101 Firefox/106.0"


@total_ordering
class Event:
    def __init__(self, date, name, address):
        self.date = arrow.get(date)
        self.name = name
        self.address = address

    def __lt__(self, other):
        return (self.date, self.name, self.address) < (
            other.date,
            other.name,
            other.address,
        )

    def __eq__(self, other):
        return (self.date, self.name, self.address) == (
            other.date,
            other.name,
            other.address,
        )

    def __hash__(self):
        return hash((self.date, self.name, self.address))


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
    ap.add_argument("-n", "--dryrun", action="store_true", help="don't write cache")
    ap.add_argument(
        "-i", "--ignore-cache", action="store_true", help="don't read cache"
    )
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
    # TODO: actually serialize Events properly
    with open(path, "w") as f:
        json.dump(
            {
                artist: [
                    (event.date.format("YYYY-MM-DD"), event.name, event.address)
                    for event in events
                ]
                for artist, events in listings.items()
            },
            f,
        )


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
    cache = {} if args.ignore_cache else read_cached(args.cache)

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
                    f"{symbol}{event.date.format('YYYY-MM-DD')}  {event.name:{namewidth}}  {event.address}"
                )
            print()

        if not args.dryrun:
            save(args.cache, dict(zip(artists, listings)))


asyncio.run(main())
