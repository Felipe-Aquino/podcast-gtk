from gi.repository import Gtk, Gdk, GdkPixbuf, GObject
import enum, os
from AudioStreamer import AudioStreamer
from font import Font

def check_create_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)


def get_gtk_image_from_file(filename, width=75, height=75, keep_ratio=True):
    img = Gtk.Image()
    pixbuf = GdkPixbuf.Pixbuf().new_from_file_at_scale(
        filename, width, height, keep_ratio)
    img.set_from_pixbuf(pixbuf)
    return img


class PlayerState(enum.Enum):
    PLAYING = 0
    PAUSED = 1
    STOPPED = 2


class Player(Gtk.Grid):
    play_img = get_gtk_image_from_file('./icons/play.png', 20, 20)
    pause_img = get_gtk_image_from_file('./icons/pause.png', 20, 20)
    stop_img = get_gtk_image_from_file('./icons/stop.png', 20, 20)

    def __init__(self):
        super(Player, self).__init__()

        self.adjustment = Gtk.Adjustment.new(0.0, 0.0, 100.0, 0.5, 10.0, 0.0)
        self.adjustment.connect('value-changed', self.on_adjustment_changed)

        self.progress = Gtk.Scale.new(Gtk.Orientation.HORIZONTAL, self.adjustment)
        self.progress.set_hexpand(True)
        self.progress.set_sensitive(False)
        self.progress.set_draw_value(False)
        self.progress.connect('button-press-event', self.on_mouse_press)
        self.progress.connect('button-release-event', self.on_mouse_release)
        
        font = Font()
        font.set_size(8)
        self.current_time = Gtk.Label('00:00:00.00', xalign=0, xpad=6)
        self.current_time.modify_font(font.to_pango_desc())
        
        self.changing_time = Gtk.Label(' ', xpad=6)
        self.changing_time.modify_font(font.to_pango_desc())

        self.total_time = Gtk.Label('00:00:00.00', xalign=1, xpad=6)
        self.total_time.modify_font(font.to_pango_desc())
        
        self.track_label = Gtk.Label(' ')

        self.play_pause_button = Gtk.Button()
        self.play_pause_button.set_image(self.play_img)
        self.play_pause_button.connect('clicked', self.play_pause_action)

        self.stop_button = Gtk.Button()
        self.stop_button.set_image(self.stop_img)
        self.stop_button.connect('clicked', self.stop_action)

        self.set_column_spacing(6)
        self.set_row_spacing(3)
        self.attach(self.track_label  , 0, 0, 3, 1)
        self.attach(self.current_time , 0, 1, 1, 1)
        self.attach(self.changing_time, 1, 1, 1, 1)
        self.attach(self.total_time   , 2, 1, 1, 1)
        self.attach(self.progress     , 0, 2, 3, 1)

        self.attach(self.play_pause_button, 3, 2, 1, 1)
        self.attach(self.stop_button      , 4, 2, 1, 1)

        self.duration = 360000000
        self.duration_str = '0'

        self.player_state = PlayerState.STOPPED

        self.player = AudioStreamer()      

        self.timeout_id = GObject.timeout_add(1000, self.on_timeout, None)

        self.mouse_moving = False


    def on_mouse_press(self, *b):
        self.mouse_moving = True

    def on_mouse_release(self, *b):
        self.changing_time.set_text('')
        self.player.set_time(int(self.duration*self.adjustment.get_value()/100))
        self.mouse_moving = False

    def on_adjustment_changed(self, adjustment):
        if self.mouse_moving:
            value = self.duration*self.adjustment.get_value()/100
            value_str = self.parse_millisecond(int(value))
            self.changing_time.set_text(value_str)

    def stop_action(self, button):
        if self.player_state != PlayerState.STOPPED:
            self.player.stop()
            self.play_pause_button.set_image(self.play_img)
            self.current_time.set_text('00:00:00.00')
            self.total_time.set_text('00:00:00.00')
            self.adjustment.set_value(0.0)
            self.progress.set_sensitive(False)
            self.player_state = PlayerState.STOPPED

    def play_pause_action(self, button):
        if self.player_state == PlayerState.STOPPED:
            self.player.play()
        elif self.player_state == PlayerState.PAUSED:
            self.player.play()
            self.player_state = PlayerState.PLAYING
            button.set_image(self.pause_img)
        else:
            self.player_state = PlayerState.PAUSED
            button.set_image(self.play_img)
            self.player.pause()

    def new_link(self, url):
        self.stop_action(None)
        self.player.new_uri(url)
        
    def parse_millisecond(self, ms):
        if isinstance(ms, int):
            s = ms / 1000
            hours = s // 3600
            minutes = (s % 3600) // 60
            seconds = (s % 3600) % 60

            return '{:02.0f}:{:02.0f}:{:05.2f}'.format(hours, minutes, seconds)
        return '00:00:00.00'

    def set_track_text(self, text):
        self.track_label.set_text(text)

    def on_timeout(self, data):
        if self.player_state == PlayerState.PLAYING:
            current = self.player.get_time()
            current_str = self.parse_millisecond(current)
            self.current_time.set_text(current_str)
            if not self.mouse_moving:
                self.adjustment.set_value(100*current / self.duration)
        elif self.player.is_playing() and self.player_state != PlayerState.PAUSED:
            self.player_state = PlayerState.PLAYING
            self.play_pause_button.set_image(self.pause_img)

            self.duration = self.player.get_duration()
            self.duration_str = self.parse_millisecond(self.duration)
            self.total_time.set_text(self.duration_str)
            self.progress.set_sensitive(True)
        elif self.adjustment.get_value() >= 99.5:
            self.stop_action(None)

        return True
