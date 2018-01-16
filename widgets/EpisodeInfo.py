from gi.repository import Gtk, Gdk
from utils import create_scrolled_window
from markup import MarkupParser

class EpisodeInfo(Gtk.Frame):
    def __init__(self, name, date, summary, *args, **kwargs):
        super(EpisodeInfo, self).__init__(label='Episode info', *args, **kwargs)

        episode_name = Gtk.Label(name, xalign=0, hexpand=1)
        episode_name.set_margin_left(12)
        episode_name.set_margin_top(6)
        episode_name.set_margin_bottom(6)

        date_label = Gtk.Label(date, xalign=1, hexpand=1)
        date_label.set_margin_right(12)
        date_label.set_margin_top(6)
        date_label.set_margin_bottom(6)

        summary_title = Gtk.Label('<span size="large"><b>Summary</b></span>', xalign=0)
        summary_title.set_margin_left(12)
        summary_title.set_use_markup(True)

        self.play_button = Gtk.Button.new_from_stock('gtk-media-play')
        self.play_button.set_margin_right(12)
        self.play_button.set_halign(Gtk.Align.END)

        m = MarkupParser()
        m.feed(summary)
        summary_info = Gtk.Label(m.markup, hexpand=1)
        summary_info.set_use_markup(True)
        summary_info.set_margin_left(12)
        summary_info.set_halign(Gtk.Align.START)
        summary_info.set_line_wrap(True)

        scrolled = create_scrolled_window(summary_info)

        grid = Gtk.Grid()
        grid.attach(episode_name    , 0, 1, 1, 1)
        grid.attach(date_label      , 1, 1, 1, 1)
        grid.attach(self.play_button, 1, 2, 1, 1)
        grid.attach(summary_title   , 0, 2, 1, 1)
        grid.attach(scrolled        , 0, 3, 2, 1)

        self.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse('#252525'))
        self.add(grid)
