from gi.repository import Gtk, Pango
from font import Font, FontWeight
from utils import parse_date


class Episode():
    def __init__(self, name, date, summary, link="", duration="0:00:00"):
        self.name = name
        self.date = parse_date(date)
        self.summary = summary
        self.link = link
        self.duration = duration

    @staticmethod
    def from_dict(d):
        episode = Episode('', 0, '')
        d.pop('podcast_id')
        for k, v in d.items():
            v = parse_date(v) if k == 'date' else v
            setattr(episode, k, v)
        return episode

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

        self.add(name)
        self.episode = episode
