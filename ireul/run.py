#!/usr/bin/env python
import gevent

from flyrc import message

from ireul.irc_bot import cli, JOIN_CHANNEL
from ireul.metainfo_readers.icy import get_metadata as get_icy_metadata
from ireul.metainfo_readers.ogg_vorbis import get_metadata as get_ogg_metadata

channels = {
    'everfree': 'http://208.67.225.10:5800/stream/1/',
    'r/a/dio': 'http://stream.r-a-dio.com:1130/main.mp3',
    'ogg-test': 'http://anka.org:8080/fresh.ogg',
}

cli.start()

gevent.sleep(3)

while True:
    for res in get_icy_metadata(channels['r/a/dio']):
        print u"Got TrackInfo: %r" % res.raw
        cli.send(message.msg(JOIN_CHANNEL, u"Now Playing: %s" % unicode(res)))
    cli.send(message.msg(JOIN_CHANNEL, "Lost connection to server."))
