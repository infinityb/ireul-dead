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
    )
from ireul.metainfo_readers.icy import get_metadata as get_icy_metadata
from ireul.metainfo_readers.ogg_vorbis import get_metadata as get_ogg_metadata
from ireul.environment import DBSession
from ireul.utils import get_now_playing_pair


channels = {
    'everfree': 'http://208.67.225.10:5800/stream/1/',
    'r/a/dio': 'http://stream.r-a-dio.com:1130/main.mp3',
    'ogg-test': 'http://anka.org:8080/fresh.ogg',
    'skys-int': 'http://vita.ib.ys:8000/cocks.ogg',
}


command_queue = gevent.queue.Queue()
session = DBSession()
track_queue = TrackQueue()
selection_strategy = RandomSelectionStrategy()
cli.add_handler(QueueHandler(track_queue, session))
cli.add_handler(NextTrackHandler(command_queue))

now_playing_getter, now_playing_transform = get_now_playing_pair()
cli.add_handler(NowPlayingHandler(now_playing_getter))
cli.start()

def send_stream_greenlet():
    send_stream(settings.STREAM_URL,
            track_getter(track_queue, 5, selection_strategy),
            post_transforms=[
                inject_events(command_queue),
                now_playing_transform,
                ],
            )

gevent.Greenlet.spawn(send_stream_greenlet)
gevent.sleep(3)

while True:
    for res in get_ogg_metadata(channels['skys-int']):
        print u"Got TrackInfo: %r" % res.raw
        if res.find_tag('x-ireul-id', False):
            ireul_id = int(res.find_tag('x-ireul-id'))
            line = u"[Track#%d] Now Playing: %s" % (ireul_id, unicode(res))
            cli.send(message.msg(JOIN_CHANNEL, line))
        else:
            cli.send(message.msg(JOIN_CHANNEL, u"Now Playing: %s" % unicode(res)))
    cli.send(message.msg(JOIN_CHANNEL, "Lost connection to server."))
