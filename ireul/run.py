#!/usr/bin/env python
import gevent

from flyrc import message
from ireul import settings
from ireul.streamer import RandomSelectionStrategy, TrackQueue, track_getter
from ireul.icy_write_vorb import send_stream
from ireul.irc_bot import cli, JOIN_CHANNEL, QueueHandler
from ireul.metainfo_readers.icy import get_metadata as get_icy_metadata
from ireul.metainfo_readers.ogg_vorbis import get_metadata as get_ogg_metadata
from ireul.environment import DBSession

channels = {
    'everfree': 'http://208.67.225.10:5800/stream/1/',
    'r/a/dio': 'http://stream.r-a-dio.com:1130/main.mp3',
    'ogg-test': 'http://anka.org:8080/fresh.ogg',
    'skys-int': 'http://vita.ib.ys:8000/cocks.ogg',
}

session = DBSession()
track_queue = TrackQueue()
selection_strategy = RandomSelectionStrategy()
cli.add_handler(QueueHandler(track_queue, session))
cli.start()

def send_stream_greenlet():
    send_stream(settings.STREAM_URL,
            track_getter(track_queue, 1, selection_strategy))

gevent.Greenlet.spawn(send_stream_greenlet)
gevent.sleep(3)

while True:
    for res in get_ogg_metadata(channels['skys-int']):
        print u"Got TrackInfo: %r" % res.raw
        if res.find_tag('x-ireul-id', False):
            ireul_id = int(res.find_tag('x-ireul-id'))
            cli.send(message.msg(JOIN_CHANNEL, u"Now Playing: %s [Track#%d]" % (unicode(res), ireul_id)))
        else:
            cli.send(message.msg(JOIN_CHANNEL, u"Now Playing: %s" % unicode(res)))
    cli.send(message.msg(JOIN_CHANNEL, "Lost connection to server."))
