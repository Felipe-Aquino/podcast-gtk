from gi.repository import Gtk, Gdk, Pango
from font import Font, FontWeight
import time, enum

class EpisodeStatus(enum.Enum):
    STOPPED = 0
    PLAYING = 1
    PAUSED = 2

class Episode():
    def __init__(self, name, date, link="", duration="0:00:00"):
        self.name = name
        self.date = date
        self.link = link
        self.duration = duration
        self.state = EpisodeStatus.STOPPED

    def to_dict(self):
        return {
            'name': self.name,
            'link': self.link,
            'date': self.date,
            'duration': self.duration
        }

    def to_list(self):
        date = time.strftime('%d/%b/%Y', self.date)
        return [self.date, self.name, self.date, self.state]

    @staticmethod
    def from_tuple(t):
        return Episode(*t)


class EpisodeRow(Gtk.ListBoxRow):
    def __init__(self, episode):
        super(EpisodeRow, self).__init__()
        
        font = Font()
        font.set_size(11)
        font.set_weight(FontWeight.BOLD)

        name = Gtk.Label(episode.name, xalign=0)
        name.modify_font(font.to_pango_desc())
        name.set_ellipsize(Pango.EllipsizeMode.END)

        date = Gtk.Label(episode.date, xalign=1)
        date.modify_fg(Gtk.StateType.NORMAL, Gdk.color_parse('#1530FF'))

        hbox = Gtk.HBox(spacing=6)
        hbox.pack_start(name, True, True, 0)
        hbox.pack_start(date, False, True, 0)

        self.add(hbox)
        self.episode = episode
