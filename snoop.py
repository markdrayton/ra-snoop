#!/usr/bin/env python3

import aiohttp
import argparse
import asyncio
import datetime
import errno
import os
import sys

from parser import parse_doc


class ArtistNotFoundError(Exception):
    pass


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
    ap.add_argument(
        "-s",
        "--start-year",
        help="start year (default %(default)s)",
        type=int,
        default=int(datetime.datetime.now().year),
    )
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


def url(artist, year):
    return f"https://www.residentadvisor.net/dj/{artist}/dates?yr={year}"


async def fetch_year(session, artist, year):
    resp = await session.request(method="GET", url=url(artist, year))
    resp.raise_for_status()
    if len(resp.history):
        # unknown artists redirect to the index page
        raise ArtistNotFoundError()
    html = await resp.text()
    return parse_doc(html)


async def fetch_listing(session, artist, start_year):
    initial = await fetch_year(session, artist, start_year)
    events = initial.events
    for year in initial.years:
        if year > start_year:
            subsequent = await fetch_year(session, artist, year)
            events.extend(subsequent.events)
    return [f"{event.date:10}  {event.name:40}  {event.address}" for event in events]


async def fetch_listings(artists, start_year):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for artist in artists:
            tasks.append(fetch_listing(session, artist, start_year))
        return await asyncio.gather(*tasks, return_exceptions=True)


async def main():
    args = parse_args()
    listings = await fetch_listings(args.artists, args.start_year)

    unknown = set()
    for artist, listing in zip(args.artists, listings):
        if isinstance(listing, ArtistNotFoundError):
            print(f"warning: unknown artist {artist}", file=sys.stderr)
            unknown.add(artist)
            continue
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
            if artist not in unknown:
                save(cache_path(args.cache, artist), listing)


asyncio.run(main())
