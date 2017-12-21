from gi.repository import Gtk, Gdk, GdkPixbuf, GObject
import enum, time, os
from AudioStreamer import AudioStreamer
from requests import file_request

def check_create_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)


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

    @staticmethod
    def from_tuple(t):
        return Episode(*t)


class EpisodeRow(Gtk.ListBoxRow):
    def __init__(self, episode):
        super(EpisodeRow, self).__init__()
        builder = Gtk.Builder.new_from_file('ui/episode.glade')
        self.add(builder.get_object('episode'))
        
        builder.get_object('name').set_text(episode.name)
        builder.get_object('date').set_text(episode.date)

        self.episode = episode


class Podcast():
    def __init__(self, name, summary, date, url='', image='images/question-mark.jpg'):
        self.name = name
        self.summary = summary
        self.date = date
        self.url = url
        self.image = image
        self.episodes = []
        self.status = Status()

    def add_episodes(self, episodes):
        self.episodes.extend(episodes)

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

    @staticmethod
    def from_tuple(t):
        return Podcast(*t)


class PodcastRow(Gtk.ListBoxRow):
    def __init__(self, podcast):
        super(PodcastRow, self).__init__()
        builder = Gtk.Builder.new_from_file('ui/podcast.glade')
        self.add(builder.get_object('podcast'))
        pixbuf = GdkPixbuf.Pixbuf().new_from_file_at_scale(podcast.image, 75, 75, True)
        builder.get_object('image').set_from_pixbuf(pixbuf)

        builder.get_object('name').set_text(podcast.name)
        builder.get_object('summary').set_text(podcast.summary)
        builder.get_object('date').set_text(podcast.date)
        self.load_revealer = builder.get_object('load_revealer')
        self.spinner = builder.get_object('spinner')

        self.podcast = podcast

    def loading(self, b):
        self.load_revealer.set_reveal_child(b)
        if b:
            self.spinner.start()
        else:
            self.spinner.stop()


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
        self.progress = builder.get_object('progress')
        self.progress.set_sensitive(False)
        self.adjustment = builder.get_object('adjustment')
        self.adjustment.connect('value-changed', self.on_adjustment_changed)
        self.progress.connect('button-press-event', self.on_mouse_press)
        self.progress.connect('button-release-event', self.on_mouse_release)

        self.current_time_label = builder.get_object('current_time_label')
        self.changing_time_label = builder.get_object('changing_time_label')
        self.total_time_label = builder.get_object('total_time_label')
        self.track_label = builder.get_object('track_label')

        self.play_pause_button = builder.get_object('play_pause_button')
        self.play_pause_button.set_image(self.play_img)
        self.play_pause_button.connect('clicked', self.play_pause_action)

        self.stop_button = builder.get_object('stop_button')
        self.stop_button.set_image(stop_img)
        self.stop_button.connect('clicked', self.stop_action)
        
        self.pack_start(builder.get_object('player_box'), False, False, 0)

        self.player_state = PlayerState.STOPPED

        self.player = AudioStreamer()      

        self.timeout_id = GObject.timeout_add(1000, self.on_timeout, None)

        self.mouse_moving = False

    def on_mouse_press(self, *b):
        self.mouse_moving = True

    def on_mouse_release(self, *b):
        self.changing_time_label.set_text('')
        self.player.set_time(int(self.duration*self.adjustment.get_value()/100))
        self.mouse_moving = False

    def on_adjustment_changed(self, adjustment):
        if self.mouse_moving:
            value = self.duration*self.adjustment.get_value()/100
            value_str = self.parse_millisecond(int(value))
            self.changing_time_label.set_text(value_str)

    def stop_action(self, button):
        if self.player_state != PlayerState.STOPPED:
            self.player.stop()
            self.play_pause_button.set_image(self.play_img)
            self.current_time_label.set_text('00:00:00.00')
            self.total_time_label.set_text('00:00:00.00')
            self.adjustment.set_value(0.0)
            self.progress.set_sensitive(False)
            self.player_state = PlayerState.STOPPED

    def play_pause_action(self, button):
        if self.player_state == PlayerState.STOPPED:
            self.player.play()
        elif self.player_state == PlayerState.PAUSED:
            self.player.play()
            self.player_state = PlayerState.PLAYING
            button.set_image(self.pause_img)
        else:
            self.player_state = PlayerState.PAUSED
            button.set_image(self.play_img)
            self.player.pause()

    def new_link(self, url):
        self.stop_action(None)
        self.player.new_uri(url)
        
    def parse_millisecond(self, ms):
        if isinstance(ms, int):
            s = ms / 1000
            hours = s // 3600
            minutes = (s % 3600) // 60
            seconds = (s % 3600) % 60

            return '{:02.0f}:{:02.0f}:{:05.2f}'.format(hours, minutes, seconds)
        return '00:00:00.00'

    def set_track_text(self, text):
        self.track_label.set_text(text)

    def on_timeout(self, data):
        if self.player_state == PlayerState.PLAYING:
            current = self.player.get_time()
            current_str = self.parse_millisecond(current)
            self.current_time_label.set_text(current_str)
            if not self.mouse_moving:
                self.adjustment.set_value(100*current / self.duration)
        elif self.player.is_playing() and self.player_state != PlayerState.PAUSED:
            self.player_state = PlayerState.PLAYING
            self.play_pause_button.set_image(self.pause_img)

            self.duration = self.player.get_duration()
            self.duration_str = self.parse_millisecond(self.duration)
            self.total_time_label.set_text(self.duration_str)
            self.progress.set_sensitive(True)
        elif self.adjustment.get_value() >= 99.5:
            self.stop_action(None)

        return True


class SearchItem(Gtk.ListBoxRow):
    def __init__(self, name, summary, date, url, image):
        super(SearchItem, self).__init__()
        builder = Gtk.Builder.new_from_file("ui/search_item.glade")
        builder.get_object('name').set_text(name)
        builder.get_object('summary').set_text(summary)
        builder.get_object('date').set_text(date)
        builder.get_object('add').connect('clicked', self.on_add_clicked)

        pixbuf = GdkPixbuf.Pixbuf().new_from_file_at_scale(image, 100, 100, True)
        builder.get_object('image').set_from_pixbuf(pixbuf)
        self.add(builder.get_object('search_item'))

        self.url = url
        
        self.add_action = None

    def link_add_action(self, action):
        self.add_action = action

    def on_add_clicked(self, button):
        if callable(self.add_action):
            self.add_action(self.url)

    @staticmethod
    def from_dict(d):
        summary = 'Artist: {} \nGenre: {} \nCountry: {}'.format(d['artistName'], d['primaryGenreName'], d['country'])
        
        date = time.strftime("%a, %d %b %Y %H:%M:%S", time.strptime(d['releaseDate'], "%Y-%m-%dT%H:%M:%SZ")) 
        image = SearchItem.get_image_from_url(d['collectionName'], d['artworkUrl100'])
        name = d['collectionName']

        return SearchItem(name, summary, date, d['feedUrl'], image)

    @staticmethod
    def get_image_from_url(img_name, url):
        default_image = './images/question-mark.jpg'

        try:
            extension = url[-3:]
            if extension in ['jpg', 'jpeg', 'png']:
                check_create_folder('./temp/images/')
                image = './temp/images/' + img_name.lower()+'.'+extension
                file_request(url, image)
                return image
            else:
                return default_image
        except:
            return default_image

        return default_image
