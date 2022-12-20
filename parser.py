import datetime
import re
from collections import namedtuple
from lxml import html
from lxml.etree import HTMLParser


Event = namedtuple("Event", "date name address")


def headx(lst):
    assert len(lst) == 1, lst
    return lst[0]


def parse_event(event):
    date = headx(event.xpath("span/text()"))
    if len(date.split(" ")) == 3:
        date = date + " " + str(datetime.datetime.now().year)
    name = headx(event.xpath("h3/a/span/text()"))
    metadata = event.xpath("div[2]//span/text()")
    address = ", ".join(metadata[:2])
    return Event(date, name, address)


def parse_tree(tree):
    spans = tree.xpath("//span")
    events = [
        span.getparent()
        for span in spans
        if span.text and re.match(r"^\w{3}, \d{2} \w{3}", span.text)
    ]
    return [parse_event(event) for event in events]


def parse_events(doc):
    tree = html.fromstring(doc, parser=HTMLParser(huge_tree=True))
    return parse_tree(tree)
