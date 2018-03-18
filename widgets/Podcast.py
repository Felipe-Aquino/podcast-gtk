from gi.repository import Gtk, Gdk, GdkPixbuf, Pango
import enum
from font import Font, FontWeight
from utils import get_gtk_image_from_file, parse_date
from widgets.Episode import Episode


DEFAULT_COVER = 'images/question-mark.jpg'


class Podcast():
    def __init__(self, id, name, summary, date, url='', image=DEFAULT_COVER):
        self.id = id
        self.name = name
        self.summary = summary
        self.date = parse_date(date)
        self.url = url
        self.image = image
        self.episodes = []

    def add_episodes(self, episodes):
        self.episodes.extend(episodes)

    @staticmethod
    def from_dict(d):
        podcast = Podcast(0, '', '', 0)
        for k, v in d.items():
            v = parse_date(v) if k == 'date' else v
            if k != 'episodes':
                setattr(podcast, k, v)

        for e in d['episodes']:
            podcast.episodes.append(Episode.from_dict(e))

        return podcast

    @staticmethod
    def from_tuple(t):
        return Podcast(*t)


class PodcastRow(Gtk.ListBoxRow):
    def __init__(self, podcast):
        super(PodcastRow, self).__init__()
        self.remove_img = get_gtk_image_from_file('./icons/delete.png', 12, 12)
        self.refresh_img = get_gtk_image_from_file('./icons/update.png', 12, 12)

        self.refresh = Gtk.Button()
        self.refresh.set_image(self.refresh_img)
        self.refresh.set_relief(Gtk.ReliefStyle.NONE)

        self.remove = Gtk.Button()
        self.remove.set_image(self.remove_img)
        self.remove.set_relief(Gtk.ReliefStyle.NONE)

        hbox1 = Gtk.HBox()
        hbox1.pack_start(self.refresh, False, True, 0)
        hbox1.pack_start(self.remove , False, True, 0)

        self.box_revealer = Gtk.Revealer()
        self.box_revealer.add(hbox1)
        self.box_revealer.set_transition_type(Gtk.RevealerTransitionType.NONE)

        hbox2 = Gtk.HBox(spacing=6)
        hbox2.pack_start(Gtk.Label(podcast.date, xalign=0), True, True, 0)
        hbox2.pack_start(self.box_revealer, True, True, 0)

        self.spinner = Gtk.Spinner()
        self.load_revealer = Gtk.Revealer.new()
        self.load_revealer.add(self.spinner)
        self.load_revealer.set_transition_type(Gtk.RevealerTransitionType.NONE)

        font = Font()
        font.set_weight(FontWeight.BOLD)
        name = Gtk.Label(podcast.name, xalign=0, yalign=0)
        name.modify_font(font.to_pango_desc())

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
        grid.attach(image   , 0, 0, 1, 3)
        grid.attach(revbox  , 1, 0, 1, 1)
        grid.attach(expander, 1, 1, 1, 1)
        grid.attach(hbox2, 1, 2, 1, 1)
        
        self.add(grid)
        self.podcast = podcast
        self.buttonsConnected = False

    def loading(self, b):
        self.load_revealer.set_reveal_child(b)
        if b:
            self.spinner.start()
        else:
            self.spinner.stop()

    def reveal_buttons(self, b):
        self.box_revealer.set_reveal_child(b)
