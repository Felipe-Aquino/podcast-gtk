from gi.repository import Gtk, Gdk, GdkPixbuf
import time, os
from font import Font, FontWeight
from utils import file_request, check_create_folder


class SearchItem(Gtk.ListBoxRow):
    def __init__(self, name, summary, date, url, image):
        super(SearchItem, self).__init__()
        
        font = Font()
        font.set_size(12)
        font.set_weight(FontWeight.BOLD)

        l_name = Gtk.Label(name, xalign=0)
        l_name.modify_font(font.to_pango_desc())
        l_summary = Gtk.Label(summary, xalign=0)
        l_date = Gtk.Label(date, xalign=0)
        b_add = Gtk.Button.new_from_stock('gtk-add')
        b_add.set_relief(Gtk.ReliefStyle.NONE)
        b_add.connect('clicked', self.on_add_clicked)
        
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(image, 100, 100, True)
        cover = Gtk.Image.new_from_pixbuf(pixbuf)
        cover.set_alignment(0,0)

        grid = Gtk.Grid(margin=6)
        grid.set_column_spacing(6)
        grid.set_row_spacing(6)
        grid.attach(cover    , 0, 0, 1, 2)
        grid.attach(b_add    , 0, 2, 1, 1)
        grid.attach(l_name   , 1, 0, 1, 1)
        grid.attach(l_summary, 1, 1, 1, 1)
        grid.attach(l_date   , 1, 2, 1, 1)
        self.add(grid)

        self.url = url
        
        self.add_action = None

    def link_add_action(self, action):
        self.add_action = action

    def on_add_clicked(self, button):
        if callable(self.add_action):
            self.add_action(self.url)

    @staticmethod
    def from_dict(d):
        summary = 'Artist: {} \nGenre: {} \nCountry: {}'.format(d['artistName'], d['primaryGenreName'], d['country'])
        
        date = time.strftime("%a, %d %b %Y %H:%M:%S", time.strptime(d['releaseDate'], "%Y-%m-%dT%H:%M:%SZ")) 
        image = SearchItem.get_image_from_url(d['collectionName'], d['artworkUrl100'])
        name = d['collectionName']

        return SearchItem(name, summary, date, d['feedUrl'], image)

    @staticmethod
    def get_image_from_url(img_name, url):
        default_image = './images/question-mark.jpg'

        try:
            extension = url[-3:]
            if extension in ['jpg', 'jpeg', 'png']:
                check_create_folder('./temp/images/')
                image = './temp/images/' + img_name.lower()+'.'+extension
                file_request(url, image)
                return image
            else:
                return default_image
        except:
            return default_image

        return default_image
