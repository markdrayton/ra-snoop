import datetime
import re
from lxml import html
from lxml.etree import HTMLParser


def monthno(month):
    months = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
    return months.index(month) + 1


def headx(lst):
    assert len(lst) == 1, lst
    return lst[0]


def parse_event(event):
    date = headx(event.xpath("span[1]/text()"))
    dateparts = date.replace(",", "").split()
    if len(dateparts) == 3:
        day = int(dateparts[1])
        month = monthno(dateparts[2])
        year = datetime.datetime.now().year
    elif len(dateparts) == 4:
        day = int(dateparts[2])
        month = monthno(dateparts[1])
        year = int(dateparts[3])
    else:
        raise ValueError(f"can't parse {date}")
    name = headx(event.xpath("h3/a/span/text()"))
    metadata = event.xpath("div[2]//span/text()")
    address = ", ".join(metadata[:2])
    return (f"{year:04}-{month:02}-{day:02}", name, address)


def parse_tree(tree):
    # find events by matching date strings
    spans = tree.xpath("//span")
    # Mon, 26 Dec
    # Sat, Feb 11, 2023
    events = [
        span.getparent()  # parent div
        for span in spans
        if span.text and re.match(r"^\w{3}, (?:\d+ \w{3}|\w{3} \d+, \d{4})$", span.text)
    ]
    return [parse_event(event) for event in events]


def parse_events(doc):
    tree = html.fromstring(doc, parser=HTMLParser(huge_tree=True))
    events = parse_tree(tree)
    # seems some events are duplicated and display: none so dedupe
    return list(set(events))
