import sys

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GLib, Gdk

from model import Podcast, Episode, Player, get_gtk_image_from_file
from api import podcast_parse, is_url, PodcastFile

PODS_FILE_NAME = 'podcasts.json'

class AppWin(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.resize(720, 540)
        self.set_position(Gtk.WindowPosition.CENTER)

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.info_box = Gtk.Box(spacing=6)

        self.podcasts = []

        self.pod_rows = []
        self.ep_rows = []

        self.podcast_box = Gtk.ListBox()
        self.podcast_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.podcast_box.connect('row-activated', self.on_podcast_selected)

        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.add_button = Gtk.Button()
        img = get_gtk_image_from_file('./icons/add.png', 10, 10) 
        self.add_button.set_image(img)
        self.add_button.connect('clicked', self.add_podcast)

        self.update_button = Gtk.Button()
        img = get_gtk_image_from_file('./icons/update.png', 10, 10) 
        self.update_button.set_image(img)
        #self.update_button.connect('clicked', self.tshow)

        self.save_button = Gtk.Button()
        img = get_gtk_image_from_file('./icons/save.png', 10, 10) 
        self.save_button.set_image(img)
        self.save_button.connect('clicked', self.on_save)

        self.podcast_entry = Gtk.Entry()
        self.podcast_entry.set_placeholder_text('Insert a new podcast feed then press the + button ->')

        bar.pack_start(self.podcast_entry, True, True, 0)
        bar.pack_start(self.add_button, False, True, 0)
        bar.pack_start(self.update_button, False, True, 0)
        bar.pack_start(self.save_button, False, True, 0)
        row = Gtk.ListBoxRow()
        row.add(bar)
        self.podcast_box.add(row)

        self.episode_box = Gtk.ListBox()
        self.episode_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.episode_box.connect('row-activated', self.on_episode_selected)

        row = Gtk.ListBoxRow()
        row.add(Gtk.Label('Episodes'))
        #row.set_selectable(False)
        self.episode_box.add(row)

        ep_scrolled_window = Gtk.ScrolledWindow()
        ep_scrolled_window.set_border_width(2)
        ep_scrolled_window.set_propagate_natural_width(True)
        ep_scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.ALWAYS)
        ep_scrolled_window.add_with_viewport(self.episode_box)

        pod_scrolled_window = Gtk.ScrolledWindow()
        pod_scrolled_window.set_border_width(2)
        pod_scrolled_window.set_propagate_natural_width(True)
        pod_scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.ALWAYS)
        pod_scrolled_window.add_with_viewport(self.podcast_box)

        self.info_box.pack_start(pod_scrolled_window, True, True, 0)
        self.info_box.pack_start(ep_scrolled_window, True, True, 0)

        self.player = Player()
        self.main_box.pack_start(self.info_box, True, True, 0)
        self.main_box.pack_start(self.player, False, False, 0)

        self.add(self.main_box)

        self.on_load()

        self.show_all()

        self.pod_selected = None
        self.pod_model_selected = None

    def add_podcast(self, button):
        url = self.podcast_entry.get_text()
        if is_url(url):
            podcast = Podcast('', '', '')
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
        file = PodcastFile(PODS_FILE_NAME)
        file.write(self.podcasts)

    def on_load(self):
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

                #self.podcast_box.show_all()
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

class App(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, application_id="podcast.gtk", **kwargs)

        self.window = None

    def do_startup(self):
        Gtk.Application.do_startup(self)

        action = Gio.SimpleAction.new('about', None)
        action.connect('activate', self.on_about)
        self.add_action(action)

        action = Gio.SimpleAction.new('quit', None)
        action.connect('activate', self.on_quit)
        self.add_action(action)

        builder = Gtk.Builder.new_from_file("menu.ui")
        self.set_app_menu(builder.get_object('app-menu'))

    def do_activate(self):
        if not self.window:
            self.window = AppWin(application=self, title="Podcast")

        self.window.present()

    def on_about(self, action, param):
        about_dialog = Gtk.AboutDialog(transient_for=self.window, modal=True)
        about_dialog.set_program_name('Podcast')
        about_dialog.set_license('LICENSE_UNKNOWN')
        about_dialog.set_website_label('GitHub')
        about_dialog.set_website('https://github.com/Felipe-Aquino/podcast-gtk')
        about_dialog.set_authors(['Felipe'])
        about_dialog.present()

    def on_quit(self, action, param):
        self.quit()


if __name__ == "__main__":
    app = App()
    app.run(sys.argv)
