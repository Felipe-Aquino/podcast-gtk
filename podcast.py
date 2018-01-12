import sys

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GLib, Gdk
from widgets.PodcastPage import PodcastPage
from widgets.SearchPage import SearchPage


class AppWin(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.resize(720, 540)
        self.set_position(Gtk.WindowPosition.CENTER)
        #self.maximize()

        hb = Gtk.HeaderBar()
        hb.set_show_close_button(True)
        hb.props.title = "Podcast"
        self.set_titlebar(hb)

        self.podcast_controller = PodcastPage()
        self.search_controller = SearchPage(self.podcast_controller)

        stack = Gtk.Stack()
        stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        stack.set_transition_duration(500)

        stack.add_titled(self.podcast_controller, "podcasts", "Podcasts")
        stack.add_titled(self.search_controller, "search", "Search")

        stack_switcher = Gtk.StackSwitcher()
        stack_switcher.set_stack(stack)
        stack_switcher.set_halign(Gtk.Align.CENTER)
        
        hb.pack_start(stack_switcher)
        self.add(stack)

        self.show_all()
        stack.set_visible_child_name('podcasts')

    def on_mouse_button_press(self, w, e):
        self.podcast_controller.on_mouse_press(w, e)


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
