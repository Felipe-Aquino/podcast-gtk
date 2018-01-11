from gi.repository import Gtk, Gdk, GdkPixbuf, Pango
import enum
from font import Font, FontWeight


DEFAULT_COVER = 'images/question-mark.jpg'


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


class Podcast():
    def __init__(self, name, summary, date, url='', image=DEFAULT_COVER):
        self.id = 0
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
    def from_tuple(t):
        return Podcast(*t)


class PodcastRow(Gtk.ListBoxRow):
    def __init__(self, podcast):
        super(PodcastRow, self).__init__()

        self.spinner = Gtk.Spinner()
        self.load_revealer = Gtk.Revealer.new()
        self.load_revealer.add(self.spinner)
        self.load_revealer.set_transition_type(Gtk.RevealerTransitionType.NONE)

        font = Font()
        font.set_weight(FontWeight.BOLD)
        name = Gtk.Label(podcast.name, xalign=0, yalign=0)
        name.modify_font(font.to_pango_desc())
        #name.modify_fg(Gtk.StateType.NORMAL, Gdk.color_parse('#FF0000'))

        revbox = Gtk.HBox(spacing=0)
        revbox.pack_start(self.load_revealer, False, True, 0)
        revbox.pack_start(name, True, True, 0)

        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(podcast.image, 75, 75, True)
        image = Gtk.Image.new_from_pixbuf(pixbuf)
        image.set_alignment(0,0)

        summary = Gtk.Label(podcast.summary, xalign=0, yalign=0)
        summary.set_max_width_chars(60)
        summary.set_lines(4)
        summary.set_ellipsize(Pango.EllipsizeMode.END)
        expander = Gtk.Expander.new('Description')
        expander.add(summary)

        grid = Gtk.Grid()
        grid.set_column_spacing(6)
        grid.attach(image, 0, 0, 1, 3)
        grid.attach(child=revbox, left = 1, top = 0, width = 1, height = 1)
        grid.attach(expander, 1, 1, 1, 1)
        grid.attach(Gtk.Label(podcast.date, xalign=0), 1, 2, 1, 1)
        
        self.add(grid)
        self.podcast = podcast

    def loading(self, b):
        self.load_revealer.set_reveal_child(b)
        if b:
            self.spinner.start()
        else:
            self.spinner.stop()
