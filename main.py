import sys

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GLib, Gdk
from widgets.PodcastPage import PodcastPage
from widgets.SearchPage import SearchPage
from widgets.Player import Player


class AppWin(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.resize(990, 550)
        self.set_position(Gtk.WindowPosition.CENTER)

        hb = Gtk.HeaderBar()
        hb.set_show_close_button(True)
        hb.props.title = "Podcast"
        self.set_titlebar(hb)

        player = Player()
        podcast_page = PodcastPage(player)
        search_page = SearchPage(podcast_page)

        stack = Gtk.Stack()
        stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        stack.set_transition_duration(500)

        stack.add_titled(podcast_page, "podcasts", "Podcasts")
        stack.add_titled(search_page, "search", "Search")

        stack_switcher = Gtk.StackSwitcher()
        stack_switcher.set_stack(stack)
        stack_switcher.set_halign(Gtk.Align.CENTER)

        hb.pack_start(stack_switcher)

        vbox = Gtk.VBox()
        vbox.pack_start(stack , True, True, 0)
        vbox.pack_start(player, False, False, 0)

        self.add(vbox)

        self.show_all()
        stack.set_visible_child_name('podcasts')


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

        builder = Gtk.Builder.new_from_file("ui/menu.ui")
        self.set_app_menu(builder.get_object('app-menu'))

    def do_activate(self):
        if not self.window:
            self.window = AppWin(application=self, title="Podcast")

        self.window.present()

    def on_about(self, action, param):
        about_dialog = Gtk.AboutDialog(transient_for = self.window, modal = True)
        about_dialog.set_program_name('Podcast')
        about_dialog.set_license_type(Gtk.License.MIT_X11)
        about_dialog.set_website_label('GitHub')
        about_dialog.set_website('https://github.com/Felipe-Aquino/podcast-gtk')
        about_dialog.set_authors(['Felipe'])
        about_dialog.run()
        about_dialog.destroy()

    def on_quit(self, action, param):
        self.quit()


if __name__ == "__main__":
    app = App()
    app.run(sys.argv)
