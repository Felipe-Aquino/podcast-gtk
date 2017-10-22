from gi.repository import Gtk, Gdk, GdkPixbuf, GObject
import enum
import font
import vlc


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
        self.layout = layout = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        layout.set_margin_bottom(5)

        info_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        l = Gtk.Label(self.name)
        f = font.Font()
        f.set_weight(font.FontWeigt.BOLD)
        f.set_size(11)
        l.modify_font(f.to_pango_desc())
        l.set_halign(Gtk.Align.START)
        info_box.pack_start(l, True, True, 0)

        l = Gtk.Label(self.date)
        f = font.Font()
        f.set_size(10)
        l.modify_font(f.to_pango_desc())
        l.modify_fg(Gtk.StateType.NORMAL, Gdk.color_parse('#1530EE'))
        l.set_halign(Gtk.Align.END)
        info_box.pack_start(l, True, True, 0)
        layout.pack_start(info_box, True, True, 0)

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
    def __init__(self, name, summary, date, image='images/question-mark.jpg'):
        self.name = name
        self.summary = summary
        self.date = date
        self.image = image
        self.episodes = []
        self.status = Status()
        self.layout = None

    def add_episodes(self, episodes):
        self.episodes.extend(episodes)

    def get_gtk_layout(self):
        self.layout = layout = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        layout.set_margin_bottom(5)

        pod_image = get_gtk_image_from_file(self.image)
        layout.pack_start(pod_image, False, False, 5)

        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        l = Gtk.Label(self.name)
        f = font.Font()
        f.set_weight(font.FontWeigt.BOLD)
        l.modify_font(f.to_pango_desc())
        l.set_halign(Gtk.Align.START)
        info_box.pack_start(l, True, True, 0)

        l = Gtk.Label(self.summary)
        l.set_halign(Gtk.Align.START)
        info_box.pack_start(l, True, True, 0)

        l = Gtk.Label(self.date)
        l.set_halign(Gtk.Align.START)
        info_box.pack_start(l, True, True, 0)

        layout.pack_start(info_box, False, False, 0)

        return layout

    def to_dict(self):
        return {
            'name': self.name,
            'summary': self.summary,
            'date': self.date,
            'image': self.image,
            'episodes': [e.to_dict() for e in self.episodes]
        }

    @staticmethod
    def from_dict(d):
        p = Podcast(d['name'], d['summary'], d['date'], d['image'])
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

        hbox = Gtk.Box()
        self.progressbar = Gtk.ProgressBar()
        self.progressbar.set_text('0:0:0.00 - 0:0:0.00')
        self.progressbar.set_show_text(True)
        hbox.pack_start(self.progressbar, True, True, 10)

        self.play_img = get_gtk_image_from_file('./icons/play.png', 20, 20)
        self.pause_img = get_gtk_image_from_file('./icons/pause.png', 20, 20)
        stop_img = get_gtk_image_from_file('./icons/stop.png', 20, 20)

        self.track_label = Gtk.Label('')
        self.pack_start(self.track_label, False, False, 2)

        self.play_pause_button = Gtk.Button()
        self.play_pause_button.set_image(self.play_img)
        self.play_pause_button.connect('clicked', self.play_pause_action)
        hbox.pack_start(self.play_pause_button, False, False, 2)

        self.stop_button = Gtk.Button()
        self.stop_button.set_image(stop_img)
        self.stop_button.connect('clicked', self.stop_action)
        hbox.pack_start(self.stop_button, False, False, 2)
        self.pack_start(hbox, False, False, 2)

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
