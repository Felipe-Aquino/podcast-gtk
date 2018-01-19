from gi.repository import Gtk, GdkPixbuf
from urllib import request
import shutil, os, time
import validators


USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'

def file_request(url, file_name):
    req = request.Request(url, data=None, headers={ 'User-Agent': USER_AGENT})

    with request.urlopen(req) as response, open(file_name, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)


def check_create_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)


def get_gtk_image_from_file(filename, width=75, height=75, keep_ratio=True):
    img = Gtk.Image()
    pixbuf = GdkPixbuf.Pixbuf().new_from_file_at_scale(
        filename, width, height, keep_ratio)
    img.set_from_pixbuf(pixbuf)
    return img


def create_scrolled_window(obj):
    viewport = Gtk.Viewport()
    viewport.add(obj)

    scrolled_window = Gtk.ScrolledWindow()
    scrolled_window.set_propagate_natural_height(True)
    scrolled_window.set_propagate_natural_width(True)
    scrolled_window.add(viewport)

    return scrolled_window


def is_url(url):
    return validators.url(url) == True


def parse_date(date):
    tm = time.localtime(date)
    return time.strftime("%a, %d %b %Y %H:%M:%S", tm)