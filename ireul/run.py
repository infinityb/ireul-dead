#!/usr/bin/env python
import gevent

from flyrc import message
from ireul import settings
from ireul.streamer import RandomSelectionStrategy, TrackQueue, track_getter
from ireul.icy_write_vorb import send_stream, inject_events
from ireul.irc_bot import cli, JOIN_CHANNEL
from ireul.irc_bot import (
        QueueHandler,
        NextTrackHandler,
        NowPlayingHandler,
        BadTrackLoggerHandler,
        FaveHandler,
    )
from ireul.metainfo_readers.icy import get_metadata as get_icy_metadata
from ireul.metainfo_readers.ogg_vorbis import get_metadata as get_ogg_metadata
from ireul.environment import DBSession
from ireul import stream_event
from ireul import ogg_trans

channels = {
    'everfree': 'http://208.67.225.10:5800/stream/1/',
    'r/a/dio': 'http://stream.r-a-dio.com:1130/main.mp3',
    'ogg-test': 'http://anka.org:8080/fresh.ogg',
    'skys-int': 'http://vita.ib.ys:8000/cocks.ogg',
    'radio-test': 'http://127.0.0.1:8000/test.ogg',
}


command_queue = gevent.queue.Queue()
session = DBSession()
track_queue = TrackQueue()
selection_strategy = RandomSelectionStrategy()

cli.add_handler(QueueHandler(track_queue, session))
cli.add_handler(NextTrackHandler(command_queue))

now_playing_getter, now_playing_transform = ogg_trans.get_now_playing_pair()
cli.add_handler(NowPlayingHandler(DBSession, now_playing_getter))
cli.add_handler(BadTrackLoggerHandler(command_queue, now_playing_getter, open('/home/sell/bad_track.txt', 'a')))
cli.add_handler(FaveHandler(DBSession, now_playing_getter))
cli.start()


def send_stream_greenlet():
    send_stream(settings.STREAM_URL,
            track_getter(track_queue, 5, selection_strategy),
            pre_transforms=[
                ogg_trans.make_seq_monotonic,
                stream_event.OggPageEvent.pre_transform,
                ],
            post_transforms=[
                ogg_trans.apply_timing,
                ogg_trans.make_pos_monotonic,
                ogg_trans.last_played_monitor(DBSession),
                stream_event.SkipTrackEvent.post_transform,
                inject_events(command_queue),
                now_playing_transform,
                ],
            )

gevent.Greenlet.spawn(send_stream_greenlet)
gevent.sleep(3)
"""
while True:
    for res in get_ogg_metadata(channels['radio-test']):
        print u"Got TrackInfo: %r" % res.raw
        if res.find_tag('x-ireul-id', False):
            ireul_id = int(res.find_tag('x-ireul-id'))
            line = u"[Track#%d] Now Playing: %s" % (ireul_id, unicode(res))
            cli.send(message.msg(JOIN_CHANNEL, line))
        else:
            cli.send(message.msg(JOIN_CHANNEL, u"Now Playing: %s" % unicode(res)))
    cli.send(message.msg(JOIN_CHANNEL, "Lost connection to server."))
"""
gevent.sleep(86400*300)
