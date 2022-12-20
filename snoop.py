#!/usr/bin/env python3

import aiohttp
import argparse
import asyncio
import datetime
import errno
import os
import sys

from parser import parse_events


UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:106.0) Gecko/20100101 Firefox/106.0"


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "-c",
        "--cache",
        default="~/.saved",
        metavar="DIR",
        type=lambda x: os.path.expanduser(x),
        help="cache dir (default %(default)s)",
    )
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
    with open(path, "w") as f:
        for line in listing:
            print(line, file=f)


def url(artist):
    return f"https://ra.co/dj/{artist}/tour-dates"


async def fetch_listing(session, artist):
    resp = await session.request(method="GET", url=url(artist))
    resp.raise_for_status()
    html = await resp.text()
    return [
        f"{event.date:10}  {event.name:50}  {event.address}"
        for event in parse_events(html)
    ]


async def fetch_listings(artists):
    async with aiohttp.ClientSession(headers={"User-Agent": UA}) as session:
        tasks = []
        for artist in artists:
            tasks.append(fetch_listing(session, artist))
        return await asyncio.gather(*tasks)


async def main():
    args = parse_args()
    listings = await fetch_listings(args.artists)

    for artist, listing in zip(args.artists, listings):
        saved = set(read_cached(cache_path(args.cache, artist)))
        scraped = set(listing)
        added = sorted(scraped - saved)
        removed = sorted(saved - scraped)
        if added or removed:
            print(f"==> {artist}")
            print()
            for line in removed:
                print(f"-{line}")
            for line in added:
                print(f"+{line}")
            print()

    if not args.dryrun:
        try:
            os.mkdir(args.cache)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        for artist, listing in zip(args.artists, listings):
            save(cache_path(args.cache, artist), listing)


asyncio.run(main())
