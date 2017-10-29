from gi.repository import Gtk, Gdk, GdkPixbuf, GObject
import enum, time, os
import font
import vlc
from requests import image_request

def check_create_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)

def break_text(text, phrase_min_size=55):
    words = text.split(' ')
    phrase_size = 0
    new_text = ''

    for word in words:
        phrase_size += len(word)

        new_text += word + ' '
        if phrase_size > phrase_min_size:
            new_text += '\n'
            phrase_size = 0

    return new_text


def get_gtk_image_from_file(filename, width=75, height=75, keep_ratio=True):
    img = Gtk.Image()
    pixbuf = GdkPixbuf.Pixbuf().new_from_file_at_scale(
        filename, width, height, keep_ratio)
    img.set_from_pixbuf(pixbuf)
    return img


class StatusType(enum.Enum):
    UNKNOWN = 'UNKOWN'
    ERROR = 'ERROR'
    SUCCESS = 'SUCCESS'


class Status():
    def __init__(self, trigger=None, *args):
        self.value = StatusType.UNKNOWN
        if callable(trigger):
            self.trigger = trigger
            self.args = args
        else:
            self.trigger = None

    def set_error(self):
        self.value = StatusType.ERROR
        if self.trigger:
            self.trigger(self, *self.args)

    def set_success(self):
        self.value = StatusType.SUCCESS
        if self.trigger:
            self.trigger(self, *self.args)

    def set_trigger(self, trigger, *args):
        if callable(trigger):
            self.trigger = trigger
            self.args = args
        else:
            self.trigger = None

    def is_error(self):
        return self.value == StatusType.ERROR

    def is_success(self):
        return self.value == StatusType.SUCCESS

    def is_unknown(self):
        return self.value == StatusType.UNKNOWN


class Episode():
    def __init__(self, name, date, link="", duration=""):
        self.name = name
        self.date = date
        self.link = link
        self.duration = duration
        self.layout = None

    def get_gtk_layout(self):
        builder = Gtk.Builder.new_from_file('ui/episode.glade')
        self.layout = layout = builder.get_object('episode')
        
        builder.get_object('name').set_text(self.name)
        builder.get_object('date').set_text(self.date)

        return layout

    def to_dict(self):
        return {
            'name': self.name,
            'link': self.link,
            'date': self.date,
            'duration': self.duration
        }

    @staticmethod
    def from_dict(d):
        return Episode(d['name'], d['date'], d['link'], d['duration'])


class Podcast():
    def __init__(self, name, summary, date, url='', image='images/question-mark.jpg'):
        self.name = name
        self.summary = summary
        self.date = date
        self.url = url
        self.image = image
        self.episodes = []
        self.status = Status()
        self.layout = None

    def add_episodes(self, episodes):
        self.episodes.extend(episodes)

    def get_gtk_layout(self):        
        builder = Gtk.Builder.new_from_file('ui/podcast.glade')
        self.layout = layout = builder.get_object('podcast')
        pixbuf = GdkPixbuf.Pixbuf().new_from_file_at_scale(self.image, 75, 75, True)
        builder.get_object('image').set_from_pixbuf(pixbuf)
        
        builder.get_object('name').set_text(self.name)
        builder.get_object('summary').set_text(self.summary)
        builder.get_object('date').set_text(self.date)
       
        return layout

    def to_dict(self):
        return {
            'name': self.name,
            'summary': self.summary,
            'date': self.date,
            'url': self.url,
            'image': self.image,
            'episodes': [e.to_dict() for e in self.episodes]
        }

    @staticmethod
    def from_dict(d):
        p = Podcast(d['name'], d['summary'], d['date'], d['url'], d['image'])
        p.add_episodes([Episode.from_dict(e) for e in d['episodes']])
        return p


class PlayerState(enum.Enum):
    PLAYING = 0
    PAUSED = 1
    STOPPED = 2


class Player(Gtk.Box):
    def __init__(self):
        super(Player, self).__init__(orientation=Gtk.Orientation.VERTICAL)

        self.duration = 360000000
        self.duration_str = 0

        self.play_img = get_gtk_image_from_file('./icons/play.png', 20, 20)
        self.pause_img = get_gtk_image_from_file('./icons/pause.png', 20, 20)
        stop_img = get_gtk_image_from_file('./icons/stop.png', 20, 20)

        builder = Gtk.Builder.new_from_file("ui/player.glade")
        self.progressbar = builder.get_object('progressbar')
        self.track_label = builder.get_object('track_label')

        self.play_pause_button = builder.get_object('play_pause_button')
        self.play_pause_button.set_image(self.play_img)
        self.play_pause_button.connect('clicked', self.play_pause_action)

        self.stop_button = builder.get_object('stop_button')
        self.stop_button.set_image(stop_img)
        self.stop_button.connect('clicked', self.stop_action)
        
        self.pack_start(builder.get_object('player_box'), False, False, 0)

        self.player_state = PlayerState.STOPPED

        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        self.media = None

        self.timeout_id = GObject.timeout_add(1000, self.on_timeout, None)

    def stop_action(self, button):
        if self.player_state != PlayerState.STOPPED:
            self.player.stop()
            self.play_pause_button.set_image(self.play_img)
            self.progressbar.set_text('0:0:0.00 - 0:0:0.00')
            self.progressbar.set_fraction(0.0)
            self.player_state = PlayerState.STOPPED

    def play_pause_action(self, button):
        if self.player_state == PlayerState.STOPPED:
            self.player.play()
        elif self.player_state == PlayerState.PAUSED:
            self.player.set_pause(0)
            self.player_state = PlayerState.PLAYING
        else:
            self.player_state = PlayerState.PAUSED
            button.set_image(self.play_img)
            self.player.set_pause(1)

    def new_link(self, url):
        try:
            self.stop_action(None)
            self.media = self.instance.media_new(url)
            self.player.set_media(self.media)
        except:
            self.media = None

    def parse_millisecond(self, ms):
        if isinstance(ms, int):
            s = ms / 1000
            hours = int(s // 3600)
            minutes = int((s % 3600) // 60)
            seconds = (s % 3600) % 60

            return str(hours) + ':' + str(minutes) + ':' + '{:2.2f}'.format(seconds)
        return '0:0:0.00'

    def set_track_text(self, text):
        self.track_label.set_text(text)

    def on_timeout(self, data):
        if self.player_state == PlayerState.PLAYING:
            current = self.player.get_time()
            current_str = self.parse_millisecond(current)
            self.progressbar.set_text(current_str + ' - ' + self.duration_str)
            self.progressbar.set_fraction(current / self.duration)

        elif self.player.is_playing():
            self.player_state = PlayerState.PLAYING
            self.play_pause_button.set_image(self.pause_img)

            self.duration = self.player.get_length()
            self.duration_str = self.parse_millisecond(self.duration)
        elif self.progressbar.get_fraction() >= 0.99:
            self.stop_action(None)

        return True


class SearchItem(Gtk.Box):
    def __init__(self, name, summary, date, url, image):
        super(SearchItem, self).__init__(orientation=Gtk.Orientation.VERTICAL)
        builder = Gtk.Builder.new_from_file("ui/search_item.glade")
        builder.get_object('name').set_text(name)
        builder.get_object('summary').set_text(summary)
        builder.get_object('date').set_text(date)

        pixbuf = GdkPixbuf.Pixbuf().new_from_file_at_scale(image, 100, 100, True)
        builder.get_object('image').set_from_pixbuf(pixbuf)
        self.pack_start(builder.get_object('search_item'), True, True, 0)

        self.url = url
         

    @staticmethod
    def from_dict(d):
        summary = 'Artist: {} \nGenre: {} \nCountry: {}'.format(d['artistName'], d['primaryGenreName'], d['country'])
        
        date = time.strftime("%a, %d %b %Y %H:%M:%S", time.strptime(d['releaseDate'], "%Y-%m-%dT%H:%M:%SZ")) 
        image = SearchItem.get_image_from_url(d['collectionName'], d['artworkUrl100'])
        name = break_text(d['collectionName'])

        return SearchItem(name, summary, date, d['feedUrl'], image)

    @staticmethod
    def get_image_from_url(img_name, url):
        default_image = './images/question-mark.jpg'

        try:
            extension = url[-3:]
            if extension in ['jpg', 'jpeg', 'png']:
                check_create_folder('./temp/images/')
                image = './temp/images/' + img_name.lower()+'.'+extension
                image_request(url, image)
                return image
            else:
                return default_image
        except:
            return default_image

        return default_image

