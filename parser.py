from collections import namedtuple
from lxml import html
from lxml.etree import HTMLParser


Event = namedtuple("Event", "date name address")
ListingData = namedtuple("ListingData", "events years")


def headx(lst):
    assert len(lst) == 1, lst
    return lst[0]


def parse_event(event):
    date, _, _ = headx(event.xpath("span/time/text()")).partition("T")
    location = headx(event.xpath("span[@itemprop='location']"))
    name = headx(location.xpath("span[@itemprop='name']//text()"))
    address = "".join(location.xpath("span[@itemprop='address']//text()"))
    return Event(date, name, address)


def parse_events(tree):
    events = tree.xpath("//article[@class='event']/div[@class='ptb4']/div[@itemscope]")
    return [parse_event(event) for event in events]


def parse_years(tree):
    years = tree.xpath(
        "//div[text()='Tour date filters']//following-sibling::div[1]/ul/li/a/text()"
    )
    return [int(year) for year in years if year.isdigit()]


def parse_doc(doc):
    tree = html.fromstring(doc, parser=HTMLParser(huge_tree=True))
    return ListingData(parse_events(tree), parse_years(tree))
