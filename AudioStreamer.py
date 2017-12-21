import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst


class AudioStreamer:
    def __init__(self):
        Gst.init(None)

        self.player = Gst.ElementFactory.make("playbin", "player")
        self.state = 'stopped'
        self.uri = None
        self.track_duration = 0.0
        self.total_time = 0.0

    def play(self):
        if self.state != 'playing' and self.uri != None:
            self.player.set_state(Gst.State.PLAYING)
            self.state = 'playing'
        elif self.uri == None:
            print("<AudioStreamer> @ play -> there's no uri to be played.")

    def pause(self):
        if self.state == 'playing':
            self.player.set_state(Gst.State.PAUSED)
            self.state = 'paused'

    def stop(self):
        if self.state != 'stopped':
            self.player.set_state(Gst.State.NULL)
            self.state = 'stopped'

    def get_time(self):
        b, time = self.player.query_position(Gst.Format.TIME)
        if not b: 
            return self.total_time
        else:
            self.total_time = time // 1000000
            return self.total_time

    def set_time(self, time):
        self.player.seek_simple(Gst.Format.TIME,  Gst.SeekFlags.FLUSH |
                                Gst.SeekFlags.KEY_UNIT, (time / 1000) * Gst.SECOND)
        self.total_time = time

    def get_duration(self):
        _, self.track_duration = self.player.query_duration(Gst.Format.TIME)        
        return self.track_duration // 1000000

    def new_uri(self, uri):
        if uri != None:
            self.uri = uri
            self.player.set_property('uri', uri)
            self.track_time = 0

    def set_volume(self, volume):
        if 0 <= volume <= 1:
            self.player.set_property('volume', volume)
        else:
            print('<AudioStreamer> @ set_volume -> volume should be between 0 and 1.')

    def get_volume(self):
        return self.player.get_property('volume')

    def is_playing(self):
        playing, _ = self.player.query_duration(Gst.Format.TIME)
        if playing and self.state == 'stopped':
            self.playing = 'playing'
        elif not playing:
            self.playing = 'stopped'
        return playing and not self.playing == 'paused'


'''
# Uncomment this code to test AudioStreamer

import time

music_stream_uri = 'https://api.soundcloud.com/tracks/58716986/stream?client_id=aa13bebc2d26491f7f8d1e77ae996a64'

streamer = AudioStreamer()
streamer.new_uri(music_stream_uri)


def go_op():
    time = input('Insert the time in ms: ')
    streamer.set_time(int(time))


def pyswitch(n):
    options = {
        '1': lambda: streamer.play(),
        '2': lambda: streamer.pause(),
        '3': lambda: streamer.stop(),
        '4': lambda: print(streamer.get_time()),
        '5': lambda: go_op()
    }
    if n in options:
        return options[n]
    return None


print('1. Play')
print('2. Pause')
print('3. Stop')
print('4. Time')
print('5. Go')
print('6. Quit')


choice = '0'
while choice != '6':
    choice = input('Pick an option (1 to 6) > ')
    f = pyswitch(choice)
    if callable(f):
        f()
'''