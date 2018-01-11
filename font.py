from enum import Enum
from gi.repository import Pango


class FontFamily(Enum):
    ''' Font families '''

    NORMAL = 'normal'
    SANS = 'sans'
    SERIF = 'serif'
    MONOSPACE = 'monospace'


class FontWeight(Enum):
    ''' Font weights '''

    ULTRA_LIGHT = 'ultralight'
    LIGHT = 'light'
    NORMAL = 'normal'
    BOLD = 'bold'
    ULTRA_BOLD = 'ultrabold'
    HEAVY = 'heavy'


class FontStyle(Enum):
    ''' Font styles '''

    NORMAL = 'normal'
    ITALIC = 'italic'
    OBLIQUE = 'oblique'


class FontStretch(Enum):
    ''' Font stretch '''

    ULTRA_CONDENSED = 'ultracondensed'
    EXTRA_CONDENSED = 'extracondensed'
    CONDENSED = 'condensed'
    SEMI_CONDENSED = 'semicondensed'
    NORMAL = 'normal'
    SEMI_EXPANDED = 'semiexpanded'
    EXPANDED = 'expanded'
    EXTRA_EXPANDED = 'extraexpanded'
    ULTRA_EXPANDED = 'ultraexpanded'


class Font():
    ''' Describes a font to be used with Gtk.Label '''

    def __init__(self):
        self.families = []
        self.styles = []
        self.weight = None
        self.stretch_style = None
        self.size = 12

    def add_family(self, family):
        ''' Add a FontFamily '''

        if family in FontFamily and not family in self.families:
            self.families.append(family)

    def add_style(self, style):
        ''' Add a FontStyle '''

        if style in FontStyle and not style in self.styles:
            self.styles.append(style)

    def set_stretch(self, stretch):
        ''' Set the FontStretch '''

        if stretch in FontStretch:
            self.stretch_style = stretch

    def set_weight(self, weight):
        ''' Set the FontWeight '''

        if weight in FontWeight:
            self.weight = weight

    def set_size(self, size):
        ''' Set the size of the font '''

        if isinstance(size, int) and size > 0:
            self.size = size

    def to_pango_desc(self):
        ''' Returns a Pango.FontDescribe object from the attributes of Font '''

        desc = ''

        if self.families:
            self.families.append(FontFamily.MONOSPACE)

        for fam in self.families:
            desc += fam.value + ','

        desc += ' '

        for stl in self.styles:
            desc += stl.value + ' '

        desc += (self.weight.value + ' ') if self.weight != None else ''
        desc += (self.stretch_style.value + ' ') if self.stretch_style != None else ''
        desc += str(self.size)

        return Pango.FontDescription(desc)
