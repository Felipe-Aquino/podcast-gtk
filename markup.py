from html.parser import HTMLParser
import re

class MarkupParser(HTMLParser):
    _replaces_ = {
        '>': '&gt',
        '<': '&lt'
    }

    _sizes_map_ = {
        'h1': 'xx-large',  
        'h2': 'x-large',  
        'h3': 'large'  
    }

    markup = ''
    start_shape = '<{tag}{attrs}>'
    end_shape = '</{}>'
    span_size_shape = '<span size=\"{}\">' 
    attrib_shape = ' {}=\"{}\"' 

    def handle_starttag(self, tag, attrs):
        if tag == 'br':
            self.markup += '\n'
        elif tag in ('h1', 'h2', 'h3'):
            self.markup += self.span_size_shape.format(self._sizes_map_[tag])
        elif tag in ('a', 'b', 'i'):
            tagged = self.start_shape.format(tag=tag, attrs='{attrs}')
            attribs = ''
            if tag == 'a':
                for attr in attrs:
                    if attr[0] == 'href':
                        attribs += self.attrib_shape.format(*attr)
                    
            self.markup += tagged.format(attrs=attribs)

    def handle_endtag(self, tag):
        if tag in ('h1', 'h2', 'h3'):
            self.markup += self.end_shape.format('span')
        elif tag in ('a', 'b', 'i'):
            self.markup += self.end_shape.format(tag)

    def handle_data(self, data):
        regex = re.compile('&')
        data = regex.sub('&amp;', data)
        for r in self._replaces_:
            regex = re.compile(r)
            data = regex.sub(self._replaces_[r], data)
        self.markup += data

    def clear_markup(self):
        self.markup = ''