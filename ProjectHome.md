## Features ##

  * gstreamer based
  * supported file types: everything supported by gstreamer (mp3, ogg, videos, ...)
  * constant pitch tempo adjustment
  * precise/quick seeking (works for videos too!)
  * position marker system
  * simple keyboard controls
  * responsive user interface due to pygame

## Installation ##

It's just a python script: [download](http://pytranscribe.googlecode.com/files/pyTranscribe.py)

Besides python you must have installed:
  * gstreamer
  * scaletempo/pitch plugins for gstreamer
  * python bindings for gstreamer
  * pygame

If you're running Ubuntu 9.04 this means you'll have to install these packages:
  * gstreamer0.10-plugins-bad
  * python-gst0.10
  * python-pygame

Ubuntu 8.04/8.10 versions of gstreamer0.10-plugins-bad do not contain the required scaletempo/pitch plugins so you'll have to compile it manually.

## Screenshot ##

![http://pytranscribe.googlecode.com/files/screenshot.jpg](http://pytranscribe.googlecode.com/files/screenshot.jpg)

## Usage ##

Start with:

`pyTranscribe.py <filename>`

Keyboard Controls:
```py

LEFT/RIGHT -> seek
BACKSPACE  -> seek to active marker (the green one) and start playing if paused
HOME       -> seek to 00:00:000
SPACE      -> pause/play
+/-        -> adjust tempo in 12-root(2) steps
F5-F10     -> set tempo to 50% - 100%
b          -> toggle scaletempo bypass
m          -> create new marker at current position
d          -> delete active marker
<ALT> +/-  -> precisely move active marker
```

The only implemented mouse control is: `LEFTMOUSEBUTTON in progress bar -> seek`
