from gi.repository import Pango
from enum import Enum


class FontFamily(Enum):
    NORMAL = 'normal'
    SANS = 'sans'
    SERIF = 'serif'
    MONOSPACE = 'monospace'


class FontWeigt(Enum):
    ULTRA_LIGHT = 'ultralight'
    LIGHT = 'light'
    NORMAL = 'normal'
    BOLD = 'bold'
    ULTRA_BOLD = 'ultrabold'
    HEAVY = 'heavy'


class FontStyle(Enum):
    NORMAL = 'normal'
    ITALIC = 'italic'
    OBLIQUE = 'oblique'


class FontStretch(Enum):
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

    def __init__(self):
        self.families = []
        self.styles = []
        self.weight = None
        self.stretch_style = None
        self.size = 12

    def add_family(self, family):
        if family in FontFamily and not family in self.families:
            self.families.append(family)

    def add_style(self, style):
        if style in FontStyle and not style in self.styles:
            self.styles.append(style)

    def set_stretch(self, stretch):
        if stretch in FontStretch:
            self.stretch_style = stretch

    def set_weight(self, weight):
        if weight in FontWeigt:
            self.weight = weight

    def set_size(self, size):
        if isinstance(size, int) and size > 0:
            self.size = size

    def to_pango_desc(self):
        desc = ''

        if len(self.families) == 0:
            self.families.append(FontFamily.MONOSPACE)

        for f in self.families:
            desc += f.value + ','

        desc += ' '

        for s in self.styles:
            desc += s.value + ' '

        desc += (self.weight.value + ' ') if self.weight != None else ''
        desc += (self.stretch_style.value + ' ') if self.stretch_style != None else ''
        desc += str(self.size)

        return Pango.FontDescription(desc)
