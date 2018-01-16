import re, os

from gi.repository import Gtk
from widgets.Podcast import Podcast, PodcastRow
from widgets.Episode import Episode, EpisodeRow
from widgets.EpisodeInfo import EpisodeInfo
from utils import check_create_folder, create_scrolled_window
from api import podcast_parse, is_url, expect_call
from database import PodcastDB


class PodcastPage(Gtk.HBox):
    def __init__(self, player, *args, **kwargs):
        super(PodcastPage, self).__init__(*args, **kwargs)

        self.player = player

        self.podcast_entry = Gtk.Entry()
        self.podcast_entry.set_placeholder_text('Insert a new podcast feed.')

        add_button = Gtk.Button.new_from_stock('gtk-add')
        add_button.connect('clicked', self.add_podcast)

        update_button = Gtk.Button.new_from_stock('gtk-refresh')
        update_button.connect('clicked', self.on_update_all)

        self.podcast_box = Gtk.ListBox()
        self.podcast_box.connect('row-activated', self.on_podcast_selected)

        podcast_sw = create_scrolled_window(self.podcast_box)

        self.episode_box = Gtk.ListBox()
        self.episode_box.connect('row-activated', self.on_episode_selected)

        self.episode_scroll = create_scrolled_window(self.episode_box)
        self.episode_scroll.connect('edge-overshot', self.on_scroll_overshot)

        self.paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        self.paned.set_position(300)
        self.paned.add1(self.episode_scroll)

        pod_hbox = Gtk.HBox()
        pod_hbox.pack_start(self.podcast_entry, True, True, 0)
        pod_hbox.pack_start(add_button        , False, True, 0)
        pod_hbox.pack_start(update_button     , False, True, 0)

        pod_vbox = Gtk.VBox()
        pod_vbox.pack_start(pod_hbox  , False, True, 0)
        pod_vbox.pack_start(podcast_sw, True, True, 0)

        ep_vbox = Gtk.VBox()
        ep_vbox.pack_start(Gtk.Label('Episodes'), False, True, 5)
        ep_vbox.pack_start(self.paned  , True, True, 0)

        self.pack_start(pod_vbox   , False, True, 3)
        self.pack_start(ep_vbox    , True, True, 3)

        check_create_folder('./temp')
        self.database = PodcastDB()
        self.on_load()

        self.pod_row_selected = None
        self.ep_selected_link = None
        self.episode_info = None

    def on_scroll_overshot(self, scroll_window, pos, *data):
        if pos == Gtk.PositionType.BOTTOM and self.pod_row_selected != None:
            for ep in self.database.fetch_more(50):
                e = Episode.from_tuple(ep)
                self.episode_box.add(EpisodeRow(e))

            self.episode_box.show_all()

    def add_podcast_from_url(self, url):
        if is_url(url) and not self.database.check_podcast_url(url):
            podcast = Podcast('', '', '', '')
            podcast.status.set_trigger(self.update_list, podcast)
            podcast_parse(url, podcast)
            self.database.insert_podcast(podcast)
            self.database.get_podcast_id(podcast)
            if podcast.id:
                self.database.insert_episodes(podcast.id, podcast.episodes)

    def add_podcast(self, button):
        url = self.podcast_entry.get_text()
        self.add_podcast_from_url(url)

    def update_list(self, status, podcast):
        if status.is_success():
            self.podcast_entry.set_text('')
            self.podcast_box.add(PodcastRow(podcast))

            self.podcast_box.show_all()

    def on_podcast_selected(self, widget, row):
        if self.pod_row_selected != row:
            if self.pod_row_selected:
                self.pod_row_selected.reveal_buttons(False)
            
            self.pod_row_selected = row
            self.pod_row_selected.reveal_buttons(True)
            if not row.buttonsConnected:
                row.remove.connect('clicked', self.on_delete_podcast)
                row.refresh.connect('clicked', self.on_update_podcast)
                row.buttonsConnected = True

            for e in self.episode_box.get_children():
                self.episode_box.remove(e)

            for ep in self.database.fetch_episodes(row.podcast.id, 50):
                e = Episode.from_tuple(ep)
                self.episode_box.add(EpisodeRow(e))

            self.episode_box.show_all()

    def on_load(self):
        try:
            for pod in self.database.fetch_pocasts():
                p = Podcast.from_tuple(pod[1:])
                p.id = pod[0]
                self.podcast_box.add(PodcastRow(p))

        except BaseException as e:
            print('Exception', e)

    def on_episode_selected(self, widget, row):
        def set_play(button):
            self.player.new_link(row.episode.link)
            text = self.pod_row_selected.podcast.name + ' > ' + row.episode.name
            self.player.set_track_text(text)
            self.player.play_pause_action(None)
        
        if self.episode_info:
            self.paned.remove(self.episode_info)
        
        episode = row.episode
        self.ep_selected_link = episode.link
        self.episode_info = EpisodeInfo(episode.name, episode.date, episode.summary)
        self.episode_info.play_button.connect('clicked', set_play)
        self.paned.add2(self.episode_info)
        self.paned.show_all()

    def on_delete_podcast(self, button):
        if self.pod_row_selected != None:
            self.database.delete_podcast(self.pod_row_selected.podcast.id)
            self.podcast_box.remove(self.pod_row_selected)
            self.pod_row_selected = None

            for e in self.episode_box.get_children():
                self.episode_box.remove(e)
                if e.episode.link == self.ep_selected_link:
                    self.ep_selected_link = None
                    self.paned.remove(self.episode_info)

    def on_update_podcast(self, button):
        sel = self.pod_row_selected
        self.on_update(sel)   
        
    def on_update_all(self, button):
        for row in self.podcast_box.get_children():
            self.on_update(row)

    def on_update(self, pod_row_update):
        def show(result, error):
            if not error:
                podcast = result
                self.database.insert_new_episodes(pod_row_update.podcast.id, podcast.episodes)
                
                if self.pod_row_selected == pod_row_update:
                    episodes = self.database.fetch_episodes(pod_row_update.podcast.id, 50)
                    for e in self.episode_box.get_children():
                        self.episode_box.remove(e)

                    for ep in episodes:
                        e = Episode.from_tuple(ep)
                        self.episode_box.add(EpisodeRow(e))

                    self.episode_box.show_all()

            pod_row_update.loading(False) 
        
        @expect_call(on_done=show)
        def updating(url):
            podcast = Podcast('', '', '', '')
            podcast_parse(url, podcast)
            return podcast

        url = pod_row_update.podcast.url
        if is_url(url):
            pod_row_update.loading(True)
            updating(url)  
