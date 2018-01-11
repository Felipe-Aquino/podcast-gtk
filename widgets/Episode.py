from gi.repository import Gtk, Gdk, GdkPixbuf
from font import Font, FontWeight
import time, enum

class EpisodeStatus(enum.Enum):
    STOPPED = 'STOPPED'
    PLAYING = 'PLAYING'
    PAUSED = 'PAUSED'

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
        
        name = Gtk.Label(episode.name, xalign=0)
        date = Gtk.Label(episode.date, xalign=1)
        
        hbox = Gtk.HBox(spacing=6)
        hbox.pack_start(name, True, True, 0)
        hbox.pack_start(date, False, True, 0)

        self.add(hbox)
        self.episode = episode
