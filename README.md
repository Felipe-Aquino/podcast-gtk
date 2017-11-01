# podcast-gtk
Just a podcast client.

![Demonstration](https://github.com/Felipe-Aquino/podcast-gtk/blob/master/demonstration.gif)

## About
Is an application capable of search, register, save and play your podcasts, once known its feeds or name.

Written in Python 3.x it uses [`Python Gtk+ 3`](http://python-gtk-3-tutorial.readthedocs.io/en/latest/) as GUI, and needs the following packages:

- [`python-vlc`](https://wiki.videolan.org/Python_bindings)
- [`feedparser`](http://pythonhosted.org/feedparser/)
- [`validators`](https://validators.readthedocs.io/en/latest/) 

You can get these packages running  `python3 -m pip install python-vlc feedparser validators` on the terminal.

## How to use
Follow these steps:

0.  Run with the command `python podcast.py`;
1.  Paste a pocast feed in the text input then press the add button (or search for it). The podcast will be saved in the local database and you can delete or update it with a mouse right-click over the selected podcast;
2.  If you select a podcast, a list of episodes will appear in the right-hand side;
3.  Select an episodes, this will show the name of the episode in the bottom bar.
4.  Once an episode selected, hit the play button and wait for 2 or 3 seconds till the audio starts to play.
