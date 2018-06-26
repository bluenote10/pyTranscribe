#!/usr/bin/python

import sys, os
import time
import pygame
import pygame.mixer
import numpy.oldnumeric
import pygst
import gst
import math
import urllib
from math import sqrt
#import wave, audioop
#import numpy
#from numpy import array,append,zeros,empty # get array type

#for font in pygame.font.get_fonts():
#    print font

def signum(int):#{{{
    if(int < 0): return -1;
    elif(int > 0): return 1;
    else: return int;
#}}}
def time2str(timeval):#{{{
    ms = timeval % 1000
    sec = (timeval / 1000) % 60
    min = timeval / (1000 * 60)
    return '%02d:%02d:%03d' % (min, sec, ms)
#}}}
def decodeMP3(infile, outfile):#{{{
    infile = os.path.abspath(infile)
    outfile = os.path.abspath(outfile)
    os.system('gst-launch filesrc location="' + infile + '" ! decodebin ! wavenc ! filesink location="' + outfile + '"')
#}}}
def applyRubberband(infile, outfile, tempo):#{{{
    infile = os.path.abspath(infile)
    outfile = os.path.abspath(outfile)
    os.system('rubberband/rubberband -T 0.8 "' + infile + '" "' + outfile + '"')
#}}}
def read_wav_file(name):#{{{
    """
    This function reads a WAV file named 'name' and returns
    an array containing integral samples.
    """

    # Open wave file for reading
    w = wave.open(name, 'rb')
    nchannels = w.getnchannels()

    # Read the wave as a raw string. Caution, this could use a
    # lot of memory!
    raw = w.readframes(w.getnframes())

    # Convert to a list of samples
    # Mono
    if nchannels == 1:
        data = empty(w.getnframes(), dtype=numpy.int16)
        for i in xrange(0, w.getnframes()):
            data[i] = audioop.getsample(raw,w.getsampwidth(),i)
    elif nchannels == 2:
        data = empty(2*w.getnframes(), dtype=numpy.int16)
        for i in xrange(0, w.getnframes()):
            data[i] = audioop.getsample(raw,w.getsampwidth(),i)

        data = array([data[0::2],data[1::2]], dtype=numpy.int16)
    return data
#}}}
def get_active_marker(markers, curpos):#{{{
    bestmarker = 0
    while bestmarker < len(markers) - 1 and markers[bestmarker + 1] <= curpos+10000000:
        bestmarker += 1
    return (bestmarker, markers[bestmarker])
#}}}
def point_in_rect(pos, rect):#{{{
    inrect = rect.collidepoint(pos)
    x = float(pos[0] - rect.left) / rect.width
    y = float(pos[1] - rect.top) / rect.height
    return inrect, x, y
#}}}

class Seeker:#{{{
    def __init__(self, duration, start, direction, slowmode):
        self.position = start
        self.direction = direction
        self.duration = duration
        self.slowmode = slowmode
        self.counter = 0

    def tick(self):
        if not self.slowmode:
            self.position += self.direction * 500000000
        else:
            #self.position += self.direction * 10000000
            self.position += self.direction * 5000000 * self.counter
            #self.position += self.direction * 10000000 * sqrt(self.counter)
        self.counter += 1
        if self.position < 0:
            self.position = 0
        if self.position > self.duration * 1000000 - 1000000000:
            self.position = self.duration * 1000000 - 1000000000

    def getPos(self):
        return self.position
#}}}

class ParseFile:#{{{
    def __init__(self, filename):

        self.playbin = gst.element_factory_make('playbin', 'playbin')
        self.playbin.set_property('uri', 'file://' + filename)

        # define a Bin that contains the fakesink
        audioline = gst.Bin('audioline')
        audioconvert = gst.element_factory_make('audioconvert', 'audioconvert')
        filter       = gst.element_factory_make('capsfilter', 'filter')
        audiosink    = gst.element_factory_make('alsasink', 'fakesink')
        #audiosink.set_property('signal-handoffs', True)
        #audiosink.set_property('silent', True)
        #audiosink.set_property('dump', True)

        caps = gst.Caps("audio/x-raw-int, channels=2, width=16, depth=16, rate=44100")
        filter.set_property("caps", caps)

        audioline.add(audioconvert, filter, audiosink)
        gst.element_link_many(audioconvert, filter, audiosink)

        pad = audioconvert.get_pad('sink')
        audioline.add_pad(gst.GhostPad('sink', pad));

        #handler_id = audiosink.connect("", self.handler, arg1, arg2)
        #audiosink.connect('handoff', handoff_cb)

        # connect the playbin to audioline
        self.playbin.set_property('audio-sink', audioline)

        bus = self.playbin.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message)

        self.done = False
        self.playbin.set_state(gst.STATE_PLAYING)

        while not self.done:
            time.sleep(0.1)

    def on_message(self, bus, message):
        t = message.type
        if t == gst.MESSAGE_EOS:
            self.playbin.set_state(gst.STATE_NULL)
            self.done = True
        elif t == gst.MESSAGE_ERROR:
            self.playbin.set_state(gst.STATE_NULL)
            err, debug = message.parse_error()
            print "Error: %s" % err, debug

def handoff_cb(sender, *args):
   print sender.get_name(), args

#}}}

class gstPlayer: # {{{
    def __init__(self, filename):

        #self.time_format = gst.Format(gst.FORMAT_TIME)

        self.playbin = gst.element_factory_make('playbin', 'playbin')
        self.playbin.set_property('uri', 'file://' + urllib.pathname2url(filename))
        #self.playbin.set_property('delay', -1000000)
        #self.playbin.set_property('uri', 'file:////home/fabian/coding/matlab/harmonics/TestRecord.mp3')
        #self.playbin.set_property('uri', 'file:///home/fabian/Desktop/Black Crowes - Remedy.mp3')

        # define a Bin that contains the scaletempo plugin
        self.audioline = gst.Bin('audioline')
        scaletempo = gst.element_factory_make('scaletempo', 'scaletempo')
        convert    = gst.element_factory_make('audioconvert', 'convert')
        resample   = gst.element_factory_make('audioresample', 'resample')
        audiosink  = gst.element_factory_make('alsasink', 'audiosink1')

        self.audioline.add(scaletempo, convert, resample, audiosink)
        gst.element_link_many(scaletempo, convert, resample, audiosink)

        pad = scaletempo.get_pad('sink')
        self.audioline.add_pad(gst.GhostPad('sink', pad));

        # define a sink for bypass
        self.bypasssink = gst.element_factory_make('alsasink', 'audiosink2')

        # connect the playbin to audioline or bypass
        self.bypass = False
        self.playbin.set_property('audio-sink', self.audioline)

        self.rate = 1.0
        self.lastpos = 0
        self.playbin.set_state(gst.STATE_PLAYING)

        #pos_int = self.playbin.query_position(self.time_format, None)[0]
        #seek_ns = pos_int + (10 * 1000000000)
        #print seek_ns
        #self.playbin.seek(0.8, self.time_format, gst.SEEK_FLAG_FLUSH, gst.SEEK_TYPE_SET, 0, gst.SEEK_TYPE_SET, seek_ns)

    def toggleBypass(self):
        pos = self.getPosition()
        self.playbin.set_state(gst.STATE_NULL)
        if self.bypass:
            self.playbin.set_property('audio-sink', self.audioline)
            self.bypass = False
        else:
            self.playbin.set_property('audio-sink', self.bypasssink)
            self.bypass = True
        self.playbin.set_state(gst.STATE_PLAYING)
        time.sleep(0.2)
        self.playbin.seek(self.rate, gst.FORMAT_TIME, gst.SEEK_FLAG_FLUSH, gst.SEEK_TYPE_SET, pos, gst.SEEK_TYPE_NONE, -1)

    def getState(self):
        return self.playbin.get_state()[1]

    def togglePause(self):
        state = self.playbin.get_state()
        #print state, gst.STATE_PLAYING, gst.STATE_PAUSED
        if state[1] == gst.STATE_PLAYING:
            self.playbin.set_state(gst.STATE_PAUSED)
        else:
            self.playbin.set_state(gst.STATE_PLAYING)

    def getDuration(self):
        try:
            query = gst.query_new_duration(gst.FORMAT_TIME)
            if self.playbin.query(query):
                total = query.parse_duration()[1]
            else: return 0
        except gst.QueryError: total = 0
        total = total / 1000000
        return total

    def getPosition(self):
        try: pos = self.playbin.query_position(gst.FORMAT_TIME)
        except gst.QueryError: pos = None

        if pos != None:
            pos = pos[0]
            self.lastpos = 0
            return pos;
        else:
            return self.lastpos

    def setrate(self):
        pos = self.getPosition()
        self.playbin.seek(self.rate, gst.FORMAT_TIME, gst.SEEK_FLAG_FLUSH, gst.SEEK_TYPE_SET, pos, gst.SEEK_TYPE_NONE, -1)

    def seek(self, seek_ns):
        #pos = self.getPosition()
        #seek_ns = pos + direction * (1 * 1000* 1000 * 1000)
        if seek_ns < 0:
            seek_ns = 0
        self.playbin.seek(self.rate, gst.FORMAT_TIME, gst.SEEK_FLAG_FLUSH, gst.SEEK_TYPE_SET, seek_ns, gst.SEEK_TYPE_NONE, -1)
        self.lastpos = seek_ns

    def on_message(self, bus, message):
        t = message.type
        if t == gst.MESSAGE_EOS:
            self.player.set_state(gst.STATE_NULL)
            self.button.set_label("Start")
        elif t == gst.MESSAGE_ERROR:
            self.player.set_state(gst.STATE_NULL)
            self.button.set_label("Start")
            err, debug = message.parse_error()
            print "Error: %s" % err, debug
#}}}

#
# Main
#

if not (len(sys.argv) > 1 and os.path.exists(sys.argv[1])):
    print 'no file specified'
    sys.exit()

filename = os.path.abspath(sys.argv[1])
#decodeMP3(filename, '/tmp/orig.wav')
#data = read_wav_file('/tmp/orig.wav')
#print data
#print data.shape
#applyRubberband('/tmp/orig.wav', '/tmp/rubberband.wav', 0.6)
#ParseFile(filename)

pygame.init();

# some constants
size = width, height = 1200, 180
color_bg = 30, 30, 30
color_font = 230, 230, 240
color_bar_bg = 0, 30, 80
color_bar_fg = 0, 130, 200
color_bar_frame = 120, 120, 120
color_marker_normal = 255, 0, 34
color_marker_active = 100, 200, 50
linespacing = 30
rect_bar = pygame.Rect(10, height - 40, width - 20, 20)

# globals
pygame.display.set_caption('pyTranscribe - ' + filename)
screen = pygame.display.set_mode(size)
clock = pygame.time.Clock()
font = pygame.font.SysFont('dejavusansmono', 14)

# start the player
player = gstPlayer(filename)

# init markers
markers = [0]

seekdir = 0
seekmarker = False
seekmarkerindex = 0

# main loop
while 1:
    screen.fill(color_bg)

    curpos = player.getPosition()
    duration = player.getDuration()

    mods = pygame.key.get_mods()
    alt_pressed = (mods & pygame.KMOD_LALT) == pygame.KMOD_LALT

    markerindex, markerstart = get_active_marker(markers, curpos)

    # event handling {{{
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            key = event.dict['key']
            scancode = event.dict['scancode']
            # print event.dict, alt_pressed
            if   key == pygame.K_HOME:
                player.seek(0)
            elif key == pygame.K_SPACE:
                player.togglePause()
            elif key == pygame.K_ESCAPE:
                sys.exit()
            # marker handling
            elif key == pygame.K_m:
                markers += [player.getPosition()]
                markers = sorted(markers)
            elif key == pygame.K_d:
                if markerindex != 0:
                    del markers[markerindex]
            elif key == pygame.K_BACKSPACE:
                player.seek(markerstart)
                if player.getState() == gst.STATE_PAUSED:
                    player.togglePause()
            # tempo adjustments
            elif key == pygame.K_KP_PLUS:
                player.rate *= math.pow(2, +1./12.)
                player.setrate()
            elif key == pygame.K_KP_MINUS:
                player.rate *= math.pow(2, -1./12.)
                player.setrate()
            elif key == pygame.K_F5:
                player.rate = 0.5
                player.setrate()
            elif key == pygame.K_F6:
                player.rate = 0.6
                player.setrate()
            elif key == pygame.K_F7:
                player.rate = 0.7
                player.setrate()
            elif key == pygame.K_F8:
                player.rate = 0.8
                player.setrate()
            elif key == pygame.K_F9:
                player.rate = 0.9
                player.setrate()
            elif key == pygame.K_F10:
                player.rate = 1.
                player.setrate()
            elif key == pygame.K_b:
                player.toggleBypass()
            # seeking
            elif key == pygame.K_LEFT:
                seekdir = -1
                if alt_pressed:
                    seekmarker = True
                    seekmarkerindex = markerindex
                    seeker = Seeker(player.getDuration(), markerstart, -1, True)
                else:
                    seekmarker = False
                    seeker = Seeker(player.getDuration(), curpos, -1, False)
            elif key == pygame.K_RIGHT:
                seekdir = +1
                if alt_pressed:
                    seekmarker = True
                    seekmarkerindex = markerindex
                    seeker = Seeker(player.getDuration(), markerstart, +1, True)
                else:
                    seekmarker = False
                    seeker = Seeker(player.getDuration(), curpos, +1, False)
        elif event.type == pygame.KEYUP:
            key = event.dict['key']
            scancode = event.dict['scancode']
            if (key == pygame.K_LEFT or key == pygame.K_RIGHT) and seekdir != 0:
                if not alt_pressed:
                    player.seek(seeker.getPos())
                    curpos = seeker.getPos()
                    markerindex, markerstart = get_active_marker(markers, curpos)
                else:
                    if seekmarkerindex != 0:
                        markers[seekmarkerindex] = seeker.getPos()
                        player.seek(seeker.getPos())
                        curpos = seeker.getPos()
                        markerindex, markerstart = get_active_marker(markers, curpos)
                seekdir = 0
        elif event.type == pygame.MOUSEBUTTONDOWN:
            inrect, x, y = point_in_rect(event.dict['pos'], rect_bar)
            if inrect:
                player.seek(int(x * duration * 1000000))
                curpos = int(x * duration * 1000000)
                markerindex, markerstart = get_active_marker(markers, curpos)

#}}}

    if seekdir != 0:
        seeker.tick()
        if alt_pressed:
            markerindex = seekmarkerindex
            if seekmarkerindex != 0:
                markers[seekmarkerindex] = seeker.getPos()
                markerstart = seeker.getPos()
            str_time = curpos / 1000000
        else:
            curpos = seeker.getPos()
            markerindex, markerstart = get_active_marker(markers, curpos)
            str_time = seeker.getPos() / 1000000
    else:
        str_time = curpos / 1000000


    # total time
    text = font.render('total time:   ' + time2str(duration), True, color_font, color_bg)
    textpos = text.get_rect(left = 40, centery = 1 * linespacing)
    screen.blit(text, textpos)

    # last marker
    text = font.render('last marker:  ' + time2str(markerstart / 1000000), True, color_font, color_bg)
    textpos = text.get_rect(left = 40, centery = 2 * linespacing)
    screen.blit(text, textpos)

    # current time
    text = font.render('current:      ' + time2str(str_time), True, color_font, color_bg)
    textpos = text.get_rect(left = 40, centery = 3 * linespacing)
    screen.blit(text, textpos)

    # fps
    text = font.render("fps:        %6.3f" % clock.get_fps(), True, color_font, color_bg)
    textpos = text.get_rect(left = 500, centery = 1 * linespacing)
    screen.blit(text, textpos)

    # tempo
    text = font.render('tempo:      %6.3f' % player.rate, True, color_font, color_bg)
    textpos = text.get_rect(left = 500, centery = 2 * linespacing)
    screen.blit(text, textpos)


    if duration != 0:
        percent_done = float(curpos) / (duration * 1000000)
    else:
        percent_done = 0
    rect_done = pygame.Rect(rect_bar)
    rect_done.width = int(percent_done * rect_bar.width)
    pygame.draw.rect(screen, color_bar_bg, rect_bar)
    pygame.draw.rect(screen, color_bar_fg, rect_done)
    pygame.draw.rect(screen, color_bar_frame, rect_bar, 1)

    for i in range(len(markers)):
        if duration != 0:
            marker_percent = float(markers[i]) / (duration * 1000000)
            marker_x = rect_bar.left + int(marker_percent * rect_bar.width)
            col = color_marker_active if i == markerindex else color_marker_normal
            points = [(marker_x, rect_bar.bottom + 3), (marker_x - 4, rect_bar.bottom + 7), (marker_x + 4, rect_bar.bottom + 7)]
            pygame.draw.polygon(screen, col, points, 0)
            points = [(marker_x, rect_bar.top    - 3), (marker_x - 4, rect_bar.top    - 7), (marker_x + 4, rect_bar.top    - 7)]
            pygame.draw.polygon(screen, col, points, 0)


    clock.tick(35)
    pygame.display.flip()














"""
ballrect = ballrect.move(speed)
if ballrect.left < 0 or ballrect.right > width:
    speed[0] = -speed[0]
if ballrect.top < 0 or ballrect.bottom > height:
    speed[1] = -speed[1]
screen.blit(ball, ballrect)
"""


# ball = pygame.image.load("ball.bmp")
# ballrect = ball.get_rect()

"""
pygame.mixer.pre_init(44100, -16, 2, 1024)
pygame.init();
pygame.mixer.music.load('/home/fabian/Desktop/Black Crowes - Remedy.mp3');
pygame.mixer.music.play();

soundfile = pygame.mixer.Sound('/home/fabian/Desktop/Black Crowes - Remedy.mp3')
length = soundfile.get_length()
channels = soundfile.get_num_channels()
pygame.sndarray.use_arraytype('numeric')
array = pygame.sndarray.array(soundfile)
print length
print array
print type(array)
print array.shape
"""


"""
self.player = gst.Pipeline("player")
source = gst.element_factory_make("filesrc", "file-source")
decoder = gst.element_factory_make("mad", "mp3-decoder")
conv1 = gst.element_factory_make("audioconvert", "converter1")
resam1 = gst.element_factory_make("audioresample", "resample1")
scaletempo = gst.element_factory_make("scaletempo", "scaletempo")
conv2 = gst.element_factory_make("audioconvert", "converter2")
resam2 = gst.element_factory_make("audioresample", "resample2")
sink = gst.element_factory_make("alsasink", "alsa-output")

self.player.add(source, decoder, conv1, resam1, scaletempo, conv2, resam2, sink)
gst.element_link_many(source, decoder, conv1, resam1, scaletempo, conv2, resam2, sink)

bus = self.player.get_bus()
bus.add_signal_watch()
bus.connect("message", self.on_message)

self.player.get_by_name("file-source").set_property("location", '/home/fabian/Desktop/Black Crowes - Remedy.mp3')
self.player.set_state(gst.STATE_PLAYING)

pos_int = self.player.query_position(self.time_format, None)[0]
seek_ns = pos_int + (10 * 1000000000)
print seek_ns
#scaletempo.seek(0.8, self.time_format, gst.SEEK_FLAG_FLUSH, gst.SEEK_TYPE_SET, 0, gst.SEEK_TYPE_SET, seek_ns)
self.player.seek(0.8, self.time_format, gst.SEEK_FLAG_FLUSH, gst.SEEK_TYPE_SET, 0, gst.SEEK_TYPE_SET, seek_ns)
#self.player.seek(0.8, self.time_format, gst.SEEK_FLAG_FLUSH, gst.SEEK_TYPE_SET, seek_ns, gst.SEEK_TYPE_NONE, gst.CLOCK_TIME_NONE)
#self.player.seek_simple(self.time_format, gst.SEEK_FLAG_FLUSH, seek_ns)

#self.player.seek(0.8, self.time_format, gst.SEEK_FLAG_FLUSH, gst.SEEK_TYPE_NONE, gst.CLOCK_TIME_NONE, gst.SEEK_TYPE_NONE, gst.CLOCK_TIME_NONE)
"""

#error = 0
#plugin = gst.plugin_load_file("/home/fabian/coding/python/soundplayer/gst-scaletempo/src/libgstscaletempoplugin.la")
#print error
#plugin.load()

#pos_int = self.playbin.query_position(self.time_format, None)[0]
#seek_ns = pos_int + (10 * 1000000000)
#print seek_ns
#self.playbin.seek(0.8, self.time_format, gst.SEEK_FLAG_FLUSH, gst.SEEK_TYPE_SET, 0, gst.SEEK_TYPE_SET, seek_ns)

