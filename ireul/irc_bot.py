from flyrc import client, handler

cli = client.SimpleClient('NotHanyuu', 'nothanyuu', '/a/radio bot',
        '10.0.12.6', 6697, ssl=True, timeout=None)
JOIN_CHANNEL = '#everfree'

cli.add_handler(handler.AutoJoin(JOIN_CHANNEL))
cli.add_handler(handler.BasicChannelCommand(prefix='-'))
# cli.add_handler(handler.QuitWhenAsked())


from flyrc import handler, message
from ireul.storage import models as m
from ireul.icy_write_vorb import SkipTrackEvent
import sqlalchemy.orm.exc as sqlao_e
class QueueHandler(object):
    DEPENDENCIES = [handler.BasicCommand]

    def __init__(self, queue, session):
        self._queue = queue
        self._sess = session

    def irc_command_show_queue(self, client, source, target, args):
        print "%r.irc_command_show_queue(%r, %r, %r, %r)" % (self, client, source, target, args)
        for track in self._queue:
            client.send(message.msg(target, track.get_name()))

    def irc_command_enqueue(self, client, source, target, args):
        print "%r.irc_command_enqueue(%r, %r, %r, %r)" % (self, client, source, target, args)
        try:
            track_id = int(args)
        except (TypeError, ValueError) as e:
            client.send(message.msg(target, "enqueue argument must parse as integral"))
        try:
            track = self._sess.query(m.TrackOriginal).filter_by(id=track_id).one()
        except sqlao_e.NoResultFound:
            client.send(message.msg(target, "track number not found"))
        client.send(message.msg(target, "track ``%s'' enqueued." % track.get_name()))
        self._queue.enqueue(track)


class NextTrackHandler(object):
    DEPENDENCIES = [handler.BasicCommand]

    def __init__(self, queue):
        self._queue = queue

    def irc_command_next(self, client, source, target, args):
        print "%r.irc_command_next(%r, %r, %r, %r)" % (self, client, source, target, args)
        self._queue.put(SkipTrackEvent())
        client.send(message.msg(target, "Okay, skipping."))


class NowPlayingHandler(object):
    DEPENDENCIES = [handler.BasicCommand]

    def __init__(self, getter):
        self._getter = getter

    def irc_command_np(self, client, source, target, args):
        print "%r.irc_command_np(%r, %r, %r, %r)" % (self, client, source, target, args)
        track, pos = self._getter()
        line = u"[Track#%d] \00313%s\017 [%d samples]" % (
                track.original._id,
                track.original.get_name(),
                pos
            )
        client.send(message.msg(target, line))
