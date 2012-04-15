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

class StreamerEvent(object):
    pass


class OggPageEvent(StreamerEvent):
    @classmethod
    def pre_transform(cls, input_event_stream):
        track = None
        pos_initial = None
        pos_cur = None
        for event in input_event_stream:
            if isinstance(event, TrackStartedEvent):
                track = event.track
                pos_initial = event.pos_initial
            if isinstance(event, cls):
                if pos_initial is None:
                    pos_initial = event.page.position
                event.track = track
                event.pos_initial = pos_initial
                event.pos_cur = event.page.position
            yield event

    def __init__(self, page, pos_i=None, pos_cur=None, track=None):
        self.page = page
        self.pos_initial = pos_i
        self.pos_cur = pos_cur
        self.track = track

    def __repr__(self):
        return "OggPageEvent(page=%r, pos_i=%r, pos_cur=%r, track=%r)" % (
                self.page, self.pos_initial, self.pos_cur, self.track)


class SkipTrackEvent(StreamerEvent):
    @classmethod
    def post_transform(cls, input_event_stream):
        skipping = False
        page_completed = False
        for event in input_event_stream:
            if isinstance(event, cls):
                print "Found SkipTrackEvent: %r" % event
                skipping = True
                page_completed = False
            if not skipping:
                yield event
            else:
                if isinstance(event, OggPageEvent):
                    page_completed = page_completed | event.page.complete
                    if not page_completed:
                        yield event
                elif isinstance(event, TrackEndedEvent):
                    print "Found TrackEndedEvent, suppressing. %r" % event
                    skipping = False
                else:
                    yield event



class TrackStartedEvent(StreamerEvent):
    def __init__(self, track, pos_initial=None):
        self.track = track
        self.pos_initial = pos_initial

    def __repr__(self):
        return "TrackStartedEvent(%r, %r)" % (
                self.track, self.pos_initial)

class TrackEndedEvent(StreamerEvent):
    def __init__(self, track, pos_initial=None):
        self.track = track
        self.pos_initial = pos_initial

    def __repr__(self):
        return "TrackEndedEvent(%r, %r)" % (
                self.track, self.pos_initial)

