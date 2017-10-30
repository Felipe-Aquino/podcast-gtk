from abc import ABC, abstractmethod
import re, os

from gi.repository import Gtk, Gdk
from model import Podcast, Episode, Player
from api import podcast_parse, is_url, PodcastFile, SearchFile
from requests import file_request

PODS_FILE_NAME = 'temp/podcasts.json'
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
        self.podcasts = []

        self.pod_rows = []
        self.ep_rows = []

        builder = Gtk.Builder.new_from_file("ui/main.glade")
        self.podcast_entry = builder.get_object('podcast_entry')
        builder.get_object('add_button').connect('clicked', self.add_podcast)
        builder.get_object('save_button').connect('clicked', self.on_save)
        #builder.get_object('update_button').connect('clicked', self.on_update)

        self.episode_box = builder.get_object('episode_box')
        self.episode_box.connect('row-activated', self.on_episode_selected)
        self.podcast_box = builder.get_object('podcast_box')
        self.podcast_box.connect('row-activated', self.on_podcast_selected)

        self.main_box = builder.get_object('main_box')
        self.player = Player()
        self.main_box.pack_start(self.player, False, False, 0)

        self.on_load()

        self.pod_selected = None
        self.pod_model_selected = None

    def get_layout(self):
        return self.main_box

    def add_podcast_from_url(self, url):
        if is_url(url):
            podcast = Podcast('', '', '', '')
            podcast.status.set_trigger(self.update_list, podcast)
            podcast_parse(url, podcast)

    def add_podcast(self, button):
        url = self.podcast_entry.get_text()
        if is_url(url):
            podcast = Podcast('', '', '', '')
            podcast.status.set_trigger(self.update_list, podcast)
            podcast_parse(url, podcast)

    def update_list(self, status, podcast):
        if status.is_success():
            self.podcast_entry.set_text('')

            self.podcasts.append(podcast)
            row = Gtk.ListBoxRow()
            row.add(podcast.get_gtk_layout())
            self.podcast_box.add(row)
            self.pod_rows.append(row)

            self.podcast_box.show_all()

    def on_podcast_selected(self, widget, row):
        p = row.get_child()
        if p != self.pod_selected:
            for pod in self.podcasts:
                if pod.layout == p:
                    for e in self.ep_rows:
                        self.episode_box.remove(e)

                    self.ep_rows = []
                    for e in pod.episodes:
                        row = Gtk.ListBoxRow()
                        row.add(e.get_gtk_layout())
                        self.episode_box.add(row)
                        self.ep_rows.append(row)

                    self.pod_selected = p
                    self.pod_model_selected = pod
                    break
            self.episode_box.show_all()

    def on_save(self, button):
        check_create_folder('./temp')
        file = PodcastFile(PODS_FILE_NAME)
        file.write(self.podcasts)

    def on_load(self):
        check_create_folder('./temp')
        file = PodcastFile(PODS_FILE_NAME)
        try:
            pods = file.read()

            if pods:
                self.podcasts.extend(pods)

                for p in self.podcasts:
                    row = Gtk.ListBoxRow()
                    row.add(p.get_gtk_layout())
                    self.podcast_box.add(row)
                    self.pod_rows.append(row)

                # self.podcast_box.show_all()
        except BaseException as e:
            print('Exception', e)

    def on_episode_selected(self, widget, row):
        p = row.get_child()

        for ep in self.pod_model_selected.episodes:
            if ep.layout == p:
                self.player.new_link(ep.link)
                text = self.pod_model_selected.name + ' > ' + ep.name
                self.player.set_track_text(text)
                break
        self.episode_box.show_all()


class SearchPageController(Controller):
    def __init__(self, pod_controller):
        builder = Gtk.Builder.new_from_file('ui/search.glade')
        self.search_box = builder.get_object('search')
        self.podcast_entry = builder.get_object('podcast_entry')
        self.search_list_box = builder.get_object('search_list_box')
        builder.get_object('search_button').connect('clicked', self.on_find)

        self.search_rows = []
        self.pod_controller = pod_controller

    def on_find(self, button):
        text = str(self.podcast_entry.get_text())

        regex = re.compile('\s+')
        text = text.lower()
        text = regex.sub('+', text)
        
        itunes_url = 'https://itunes.apple.com/search?term={}&media=podcast'.format(text)

        try:
            check_create_folder('./temp')

            file_request(itunes_url, SEARCH_FILE_NAME)
            file = SearchFile(SEARCH_FILE_NAME)
            results = file.read()

            for row in self.search_rows:
                self.search_list_box.remove(row)
            del self.search_rows
            self.search_rows = []
            for r in results:
                row = Gtk.ListBoxRow()
                row.add(r)
                r.link_add_action(self.pod_controller.add_podcast_from_url)
                self.search_list_box.add(row)
                self.search_rows.append(row)
            self.search_list_box.show_all()

        except BaseException as e:
            print('Exception', e)

    def get_layout(self):
        return self.search_box

    