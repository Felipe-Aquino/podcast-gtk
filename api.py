import time, threading, json
import feedparser
from widgets.Podcast import Podcast, DEFAULT_COVER
from widgets.Episode import Episode
from widgets.SearchItem import SearchItem 
from utils import file_request
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

def get_summary(episode_entry):
    if 'summary' in episode_entry:
        return episode_entry['summary']
    elif 'summary_detail' in episode_entry:
        detail = episode_entry['summary_detail']
        if 'value' in detail:
            return detail['value']
    return 'No summary given!'

def get_date(feed_dict):
    date = time.gmtime()
    if 'published_parsed' in feed_dict:
        date = feed_dict['published_parsed']
    elif 'updated_parsed' in feed_dict:
        date = feed_dict['updated_parsed']
    elif 'pubDate' in feed_dict:
        date = feed_dict['pubDate']

    return time.mktime(date)


def get_link(feed_dict):
    link = ''
    if 'links' in feed_dict:
        for l in feed_dict['links']:
            if 'type' in l and l['type'] in AUDIO_TYPES:
                link = l['href'] if 'href' in l else ''

    return link


def get_image_from_feed(feed):
    try:
        image_url = feed['image']['href']
        extension = image_url[-3:]
        if extension in ['jpg', 'jpeg', 'png']:
            image = './images/' + feed['title'].lower() + '.' + extension
            file_request(image_url, image)
            return image
    except:
        pass

    return DEFAULT_COVER

def extract_episodes(entries):
    episodes = []
    for entry in entries:
        if entry:
            episodes.append({
                'name': entry['title'],
                'date': get_date(entry),
                'summary': get_summary(entry),
                'link': get_link(entry),
                'duration': entry['itunes_duration'] if 'itunes_duration' in entry else ''
            })
    
    return episodes

def save_podcast(url):
    response = feedparser.parse(url)

    if response:
        feed = response['feed']
        podcast = {}
        podcast['name'] = feed['title']
        podcast['summary'] = feed['summary'] if 'summary' in feed else feed['title']
        podcast['date'] = get_date(feed)
        podcast['url'] = url
        podcast['image'] = get_image_from_feed(feed)
        podcast['episodes'] = extract_episodes(response['entries'])
        return podcast
    
    return {}


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
