import random
import time
import itertools
import gevent
import urlparse
from ireul.helpers.net import resolve_netloc
from gevent import socket
from mutagen.ogg import OggPage
from mutagen.oggvorbis import OggVorbisInfo, TryNextPage
from mutagen._vorbis import VCommentDict, VComment
from cStringIO import StringIO
from base64 import b64encode
from .stream_event import (
        StreamerEvent,
        OggPageEvent,
        SkipTrackEvent,
        TrackStartedEvent
    )

compose = lambda *fx: reduce(lambda f, g: lambda *args, **kwargs: f(g(*args, **kwargs)), fx)


def create_metadata_packet(tags):
    vc = VComment()
    vc.extend(tags)
    return "\x03vorbis"+vc.write()

def yield_events(track_derived):
    fh = track_derived.open()
    yield TrackStartedEvent(track_derived)
    yield OggPageEvent(OggPage(fh))
    tmp = OggPage(fh)
    # replace outgoing tag
    tmp.packets[0] = create_metadata_packet([
        ('title', track_derived.original.title),
        ('album', track_derived.original.metadata.album_name),
        ('artist', track_derived.original.artist),
        ('x-ireul-id', unicode(track_derived.id))])
    yield OggPageEvent(tmp)
    try:
        while True:
            yield OggPageEvent(OggPage(fh))
    except EOFError:
        pass


def inject_events(event_queue):
    def _injector(input_event_stream):
        for event in input_event_stream:
             if not event_queue.empty():
                 yield event_queue.get()
             yield event
    return _injector



def ogg_show_event(input_event_stream):
    for event in input_event_stream:
        print repr(event)
        yield event

def ogg_make_pos_monotonic(input_event_stream):
    track_offset = None
    last_pos = 0
    for event in input_event_stream:
        if isinstance(event, OggPageEvent):
            if event.page.position == 0: # starting a new track
                track_offset = last_pos
            event.page.position = last_pos = track_offset + event.page.position
        yield event

def ogg_make_seq_monotonic(input_event_stream):
    seq_ctr = itertools.count()
    for event in input_event_stream:
        if isinstance(event, OggPageEvent):
            event.page.sequence = next(seq_ctr)
        yield event

def ogg_make_single_serial(input_event_stream):
    serial = random.randint(0, 2**32)
    for event in input_event_stream:
        if isinstance(event, OggPageEvent):
            event.page.serial = serial
        yield event

def ogg_fix_header(input_event_stream):
    yield next(input_event_stream)
    for event in input_event_stream:
        event.page.first = False
        yield event

""" Broken
def monitor_position(input_event_stream):
    event = next(input_event_stream)
    yield event
    t_initial = time.time()
    prev_pos = event.page.position
    time_sum = 0
    for event in input_event_stream:
        if isinstance(event, OggPageEvent):

        delta = event.page.position - prev_pos
        time_sum += float(delta)/44100
        wall_clock_delta = time.time() - t_initial - float(event.page.position)/44100
        print "serial=%d pos=%d time_delta=%.3fs pos_delta = %d samples, %0.3fs"  % (
                event.page.serial, event.page.position, wall_clock_delta, delta, float(delta)/44100)
        prev_pos = event.page.position
        yield event
    print "total position = %d" % prev_pos
    print "total time = %dm:%02.2fs" % divmod(time_sum, 60)
"""

def apply_timing(input_event_stream):
    time_initial = time.time()
    for event in input_event_stream:
        if isinstance(event, OggPageEvent):
            real_time = time.time() - time_initial
            play_time = float(event.page.position)/44100
            gevent.sleep(max(0.0, play_time - real_time))
        yield event


def send_stream(url, source_file_iter, pre_transforms=[], post_transforms=[]):
    """Returns an iterable yielding the ICY metadata"""
    parse_result = urlparse.urlparse(url)
    netloc = parse_result.netloc
    user_pass = None
    if '@' in netloc:
        user_pass, netloc = parse_result.netloc.split('@')
    hostname, addresses = resolve_netloc(netloc)
    conn = None
    for af, address in addresses:
        conn = socket.socket(af, socket.SOCK_STREAM)
        try:
            conn.connect(address)
            break
        except socket.error:
            continue
    conn.send("SOURCE {mount} HTTP/1.0\r\n".format(mount=parse_result.path))
    if user_pass:
        conn.send("Authorization: Basic %s\r\n" % b64encode(user_pass))
    conn.send("HOST: {hostname}\r\n".format(hostname=hostname))
    conn.send("User-Agent: ireul\r\n")
    conn.send("Content-Type: application/ogg\r\n")
    conn.send("\r\n")

    fileobj = conn.makefile()
    fileobj.readline()
    fileobj.readline()


    ogg_event_pre = compose(
            ogg_make_seq_monotonic,
            OggPageEvent.pre_transform,
            *pre_transforms
            )

    ogg_event_post = compose(
            apply_timing,
            ogg_make_pos_monotonic,
            SkipTrackEvent.post_transform,
            *post_transforms
            )

    # get all the pages
    def stream_events():
        for track_derived in source_file_iter:
            for event in ogg_event_pre(yield_events(track_derived)):
                yield event

    # apply transforms and write them out
    for event in ogg_event_post(stream_events()):
        #import pdb; pdb.set_trace()
        if isinstance(event, OggPageEvent):
            fileobj.write(event.page.write())
        print "event : %r" % event

