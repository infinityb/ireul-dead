from flyrc import client, handler

cli = client.SimpleClient('NotHanyuu', 'nothanyuu', '/a/radio bot',
                          '10.0.12.6', 6697, ssl=True, timeout=None)
JOIN_CHANNEL = '#everfree'

cli.add_handler(handler.AutoJoin(JOIN_CHANNEL))
cli.add_handler(handler.BasicChannelCommand(prefix='!'))
# cli.add_handler(handler.QuitWhenAsked())

from flyrc import handler, message
import sqlalchemy.orm.exc as sqlao_e
class QueueHandler(object):
    DEPENDENCIES = [handler.BasicCommand]

    def __init__(self, queue, session):
        self._queue = queue
        self._sess = session

    def irc_command_show_queue(self, client, source, target, args):
        for track in self._queue:
            client.send(message.msg(JOIN_CHANNEL, track.get_name()))

    def irc_command_enqueue(self, client, source, target, args):
        try:
            track_id = int(args)
        except (TypeError, ValueError) as e:
            client.send(message.msg(JOIN_CHANNEL, "enqueue argument must parse as integral"))
        try:
             track = self._sess.query(m.TrackOriginal).filter_by(id=track_id).one()
        except sqlao_e.NoResultFound:
            client.send(message.msg(JOIN_CHANNEL, "track number not found"))
        self._queue.enqueue(track)
