from abc import ABC, abstractmethod
import re
import os

from gi.repository import Gtk, Gdk, GObject
from model import Podcast, PodcastRow, Episode, EpisodeRow, Player
from api import podcast_parse, is_url, expect, SearchFile
from requests import file_request
from database import PodcastDB

SEARCH_FILE_NAME = 'temp/searched.json'


def check_create_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)


class Controller(ABC):
    @abstractmethod
    def get_layout(self):
        pass


class PodcastPageController(Controller):
    def __init__(self):
        builder = Gtk.Builder.new_from_file("ui/main.glade")
        self.podcast_entry = builder.get_object('podcast_entry')
        builder.get_object('add_button').connect('clicked', self.add_podcast)
        #builder.get_object('update_button').connect('clicked', self.on_update)

        self.episode_box = builder.get_object('episode_box')
        self.episode_box.connect('row-activated', self.on_episode_selected)
        self.podcast_box = builder.get_object('podcast_box')
        self.podcast_box.connect('row-activated', self.on_podcast_selected)

        self.main_box = builder.get_object('main_box')
        self.player = Player()
        self.main_box.pack_start(self.player, False, False, 0)

        check_create_folder('./temp')
        self.database = PodcastDB()
        self.on_load()

        self.pod_row_selected = None

        builder = Gtk.Builder.new_from_file('ui/popup.glade')
        builder.get_object('update_button').connect('clicked', self.on_update_podcast)
        builder.get_object('delete_button').connect('clicked', self.on_delete_podcast)
        self.popup = builder.get_object('popup')

    def get_layout(self):
        return self.main_box

    def add_podcast_from_url(self, url):
        if is_url(url) and not self.database.check_podcast_url(url):
            podcast = Podcast('', '', '', '')
            podcast.status.set_trigger(self.update_list, podcast)
            podcast_parse(url, podcast)
            self.database.insert_podcast(podcast)
            pod_id = self.database.get_podcast_id(podcast)
            if pod_id:
                self.database.insert_episodes(pod_id[0], podcast.episodes)

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
            self.pod_row_selected = row

            for e in self.episode_box:
                self.episode_box.remove(e)

            pod_id = self.database.get_podcast_id(row.podcast)
            for ep in self.database.fetch_episodes(pod_id[0], 50):
                e = Episode.from_tuple(ep)
                self.episode_box.add(EpisodeRow(e))

            self.episode_box.show_all()

    def on_load(self):
        try:
            for pod in self.database.fetch_pocasts():
                episodes = self.database.fetch_episodes(pod[0], 50)
                p = Podcast.from_tuple(pod[1:])
                p.add_episodes([Episode.from_tuple(e) for e in episodes])

                self.podcast_box.add(PodcastRow(p))

        except BaseException as e:
            print('Exception', e)

    def on_episode_selected(self, widget, row):
        self.player.new_link(row.episode.link)
        text = self.pod_row_selected.podcast.name + ' > ' + row.episode.name
        self.player.set_track_text(text)

    def on_mouse_press(self, w, e):
        if e.button == 3 and self.pod_row_selected != None:
            self.popup.set_relative_to(self.pod_row_selected.get_child())
            self.popup.popup()

    def on_delete_podcast(self, button):
        if self.pod_row_selected != None:
            pod_id = self.database.get_podcast_id(
                self.pod_row_selected.podcast)
            self.database.delete_podcast(pod_id[0])
            self.podcast_box.remove(self.pod_row_selected)
            self.pod_row_selected = None

            for e in self.episode_box:
                self.episode_box.remove(e)

            self.player.set_track_text('')

    def on_update_podcast(self, button):
        if self.pod_row_selected != None:
            url = self.pod_row_selected.podcast.url
            if is_url(url):
                podcast = self.pod_row_selected.podcast
                podcast_parse(url, podcast)
                pod_id = self.database.get_podcast_id(podcast)
                self.database.insert_new_episodes(pod_id[0], podcast.episodes)

                for e in self.episode_box:
                    self.episode_box.remove(e)

                for ep in self.database.fetch_episodes(pod_id[0], 50):
                    e = Episode.from_tuple(ep)
                    self.episode_box.add(EpisodeRow(e))

                self.episode_box.show_all()
            self.popup.popdown()


class SearchPageController(Controller):
    def __init__(self, pod_controller):
        builder = Gtk.Builder.new_from_file('ui/search.glade')
        self.search_box = builder.get_object('search')
        self.podcast_entry = builder.get_object('podcast_entry')
        self.podcast_entry.connect('activate', self.on_find)
        self.search_list_box = builder.get_object('search_list_box')
        self.spinner = builder.get_object('spinner')

        self.search_rows = []
        self.pod_controller = pod_controller

    def on_find(self, button):
        self.spinner.start()
        text = str(self.podcast_entry.get_text())

        regex = re.compile('\s+')
        text = text.lower()
        text = regex.sub('+', text)

        itunes_url = 'https://itunes.apple.com/search?term={}&media=podcast'.format(
            text)

        def updating_list(results):
            for row in self.search_rows:
                self.search_list_box.remove(row)
            self.search_rows = []
            for r in results:
                row = Gtk.ListBoxRow()
                row.add(r)
                r.link_add_action(self.pod_controller.add_podcast_from_url)
                self.search_list_box.add(row)
                self.search_rows.append(row)
            self.search_list_box.show_all()
            self.spinner.stop()

        @expect
        def requesting():
            file_request(itunes_url, SEARCH_FILE_NAME)
            file = SearchFile(SEARCH_FILE_NAME)
            results = file.read()

            GObject.idle_add(lambda: updating_list(results))

        try:
            check_create_folder('./temp')

            requesting()

        except BaseException as e:
            print('Exception', e)

    def get_layout(self):
        return self.search_box
