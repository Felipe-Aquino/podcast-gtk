import time, threading, json
import feedparser
from model import Podcast, Episode, SearchItem
from requests import file_request
import validators
from gi.repository import GObject

def expect(fn):
    def wrapped(*args):
        threading.Thread(target=fn, args=args).start()
    return wrapped

def async_call(f, on_done):
    def call():
        result, error = None, None

        try:
            result = f()
        except BaseException as e:
            error = e

        GObject.idle_add(lambda: on_done(result, error))

    threading.Thread(target=call).start()

def expect_call(on_done = lambda r, e: None):
    def wrapped(fn):
        def run(*args):
            async_call(lambda: fn(*args), on_done)
        return run
    return wrapped


AUDIO_TYPES = ['audio/mpeg', 'audio/x-m4a']


def get_date(feed_dict):
    date = time.gmtime()
    if 'published_parsed' in feed_dict:
        date = feed_dict['published_parsed']
    elif 'updated_parsed' in feed_dict:
        date = feed_dict['updated_parsed']
    elif 'pubDate' in feed_dict:
        date = feed_dict['pubDate']

    return time.strftime("%a, %d %b %Y %H:%M:%S", date)


def get_link(feed_dict):
    link = ''
    if 'links' in feed_dict:
        for l in feed_dict['links']:
            if 'type' in l and l['type'] in AUDIO_TYPES:
                link = l['href'] if 'href' in l else ''

    return link


def set_image_from_feed(feed, podcast):
    default_image = './images/question-mark.jpg'

    try:
        image_url = feed['image']['href']
        extension = image_url[-3:]
        if extension in ['jpg', 'jpeg', 'png']:
            podcast.image = './images/' + \
                feed['title'].lower() + '.' + extension
            file_request(image_url, podcast.image)
        else:
            podcast.image = default_image
    except:
        podcast.image = default_image


def populate_episodes(entries, podcast):
    episodes = []
    for entry in entries:
        if entry:
            episodes.append(Episode(
                name=entry['title'],
                date=get_date(entry),
                link=get_link(entry),
                duration=entry['itunes_duration'] if 'itunes_duration' in entry else ''
            ))
        
    podcast.episodes = []
    podcast.add_episodes(episodes)


# @expect
def podcast_parse(url, podcast):
    response = feedparser.parse(url)

    if response:
        feed = response['feed']
        podcast.name = feed['title']
        summary = feed['summary'] if 'summary' in feed else feed['title']
        podcast.summary = summary
        podcast.date = get_date(feed)
        podcast.url = url

        set_image_from_feed(feed, podcast)

        entries = response['entries']
        populate_episodes(entries, podcast)

        podcast.status.set_success()
    else:
        podcast.status.set_error()


def is_url(url):
    return validators.url(url) == True


class SearchFile:
    def __init__(self, file_name):
        self.file_name = file_name

    def read(self):
        searched = {"resultCount": 0, "results": []}
        items = []
        with open(self.file_name, 'r') as file:
            searched = json.load(file)
    
        for s in searched['results']:
            if 'feedUrl' in s:
                items.append(SearchItem.from_dict(s))
        return items
