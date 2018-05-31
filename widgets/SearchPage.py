import re

from gi.repository import Gtk
from api import expect_call, SearchFile
from utils import file_request, create_scrolled_window

SEARCH_FILE_NAME = 'temp/searched.json'
ITUNES_URL = 'https://itunes.apple.com/search?term={}&media=podcast'


class SearchPage(Gtk.VBox):
    def __init__(self, podcast_page, *args, **kwargs):
        super(SearchPage, self).__init__(*args, **kwargs)

        self.podcast_entry = Gtk.Entry()
        self.podcast_entry.set_icon_from_stock(Gtk.EntryIconPosition.PRIMARY, 'gtk-find')
        self.podcast_entry.set_placeholder_text('Insert a new podcast feed.')
        self.podcast_entry.connect('activate', self.on_find)

        self.search_list_box = Gtk.ListBox()
        self.spinner = Gtk.Spinner()
        self.spinner.start()

        self.spinner_rev = Gtk.Revealer.new()
        self.spinner_rev.set_transition_type(Gtk.RevealerTransitionType.NONE)
        self.spinner_rev.add(self.spinner)

        search_sw = create_scrolled_window(self.search_list_box)

        hbox = Gtk.HBox()
        hbox.pack_start(self.podcast_entry, True, True, 3)
        hbox.pack_start(self.spinner_rev  , False, True, 3)

        self.pack_start(hbox     , False, True, 0)
        self.pack_start(search_sw, True, True, 0)

        self.podcast_page = podcast_page

    def on_find(self, button):
        self.spinner_rev.set_reveal_child(True)
        text = str(self.podcast_entry.get_text())

        regex = re.compile('\s+')
        text = text.lower()
        text = regex.sub('+', text)

        itunes_url = ITUNES_URL.format(text)

        def updating_list(results, error):
            if not error:
                for row in self.search_list_box.get_children():
                    self.search_list_box.remove(row)
                for r in results:
                    r.link_add_action(self.podcast_page.add_podcast_from_url)
                    self.search_list_box.add(r)
                self.search_list_box.show_all()
            self.spinner_rev.set_reveal_child(False)

        @expect_call(on_done=updating_list)
        def requesting():
            file_request(itunes_url, SEARCH_FILE_NAME)
            file = SearchFile(SEARCH_FILE_NAME)
            return file.read()

        requesting()

