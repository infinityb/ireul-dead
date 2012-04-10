#!/usr/bin/env python
import gevent

from flyrc import message

from hanyuu2.irc_bot import cli
from hanyuu2.icy_read import get_icy_metadata

channels = {
    'everfree': 'http://208.67.225.10:5800/stream/1/',
    'r/a/dio': 'http://stream.r-a-dio.com:1130/main.mp3'
}

cli.start()

gevent.sleep(3)

while True:
    for res in get_icy_metadata(channels['everfree']):
        print "Got TrackInfo: %r" % res.raw
        cli.send(message.msg("#everfree", "Now Playing: %s" % str(res)))
    cli.send(message.msg("#everfree", "Lost connection to server."))
