from lxml import html
from lxml.etree import HTMLParser
import requests

def headx(lst):
    assert len(lst) == 1, lst
    return lst[0]

def url(artist):
    return "https://www.residentadvisor.net/dj/{}/dates?yr=2019".format(artist)

def parse_event(event):
    date, _, _ = headx(event.xpath("span/time/text()")).partition("T")
    location = headx(event.xpath("span[@itemprop='location']"))
    name = headx(location.xpath("span[@itemprop='name']//text()"))
    address = "".join(location.xpath("span[@itemprop='address']//text()"))
    return (date, name, address)

def parse_events(tree):
    events = tree.xpath(
        "//article[@class='event']/div[@class='ptb4']/div[@itemscope]"
    )
    for event in events:
        yield parse_event(event)

def scrape(artist):
    page = requests.get(url(artist))
    tree = html.fromstring(page.content, parser=HTMLParser(huge_tree=True))
    return ["{:10}  {:40}  {}".format(*event) for event in parse_events(tree)]
