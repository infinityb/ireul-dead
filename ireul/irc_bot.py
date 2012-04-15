from flyrc import client, handler

cli = client.SimpleClient('Ireul', 'nothanyuu', '/a/radio bot',
        'irc.yasashiisyndicate.org', 6697, ssl=True, timeout=None)
JOIN_CHANNEL = '#'

cli.add_handler(handler.AutoJoin(JOIN_CHANNEL))
cli.add_handler(handler.BasicChannelCommand(prefix='.'))
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

    def __init__(self, session_factory, getter):
        self._sessf = session_factory
        self._getter = getter

    def irc_command_np(self, client, source, target, args):
        print "%r.irc_command_np(%r, %r, %r, %r)" % (self, client, source, target, args)
        track, pos = self._getter()
        session = self._sessf()
        try:
            track = session.merge(track)
            line = u"[Track#%d] \00313%s\017 [%d samples] [faves \0033+%d\017]" % (
                track.original._id,
                track.original.get_name(),
                pos,
                track.original.faves.count(),
            )
            client.send(message.msg(target, line))
        finally:
            session.close()


class BadTrackLoggerHandler(object):
    DEPENDENCIES = [handler.BasicCommand]

    def __init__(self, cmd_queue, getter, out_file):
        self._queue = cmd_queue
        self._getter = getter
        self._out_file = out_file

    def irc_command_badtrack(self, client, source, target, args):
        print "%r.irc_command_np(%r, %r, %r, %r)" % (self, client, source, target, args)
        track, pos = self._getter()
        
        self._out_file.write("%s\t%d\n" % (source, track.original._id))
        self._out_file.flush()
        self._queue.put(SkipTrackEvent())
        client.send(message.msg(target, "track logged and skipped"))

class FaveHandler(object):
    DEPENDENCIES = [handler.BasicCommand]
    def __init__(self, session_factory, getter):
        self._sessf = session_factory
        self._getter = getter

    def irc_command_fave(self, client, source, target, args):
        session = self._sessf()
        username = u"%s@%s" % (source.nick, client.host)
        track, pos = self._getter()
        try:
            track = session.merge(track)
            try:
                user = session.query(m.User).\
                        filter(m.User.username==username).one()
            except sqlao_e.NoResultFound:
                user = m.User(username=username)
                session.add(user)
            try:
                fave = m.Fave(user=user, track=track.original)
                session.add(fave)
                client.send(message.msg(target, u"%s: marked %s as fave" % (
                        source.nick, track.original.get_name())))
                session.commit()
            except Exception as e:
                client.send(message.msg(target, u"%s: an error occured: %r" % (
                        source.nick, e)))
        finally:
            session.close()

    def irc_command_unfave(self, client, source, target, args):
        session = self._sessf()
        username = u"%s@%s" % (source.nick, client.host)
        track, pos = self._getter()
        try:
            track = session.merge(track)
            try:
                user = session.query(m.User).\
                        filter(m.User.username==username).one()
                fave_rec = session.query(m.Fave).\
                        filter(m.Fave.user == user).\
                        filter(m.Fave.track == track.original).one()
                session.delete(fave_rec)
                session.commit()
                client.send(message.msg(target, u"%s: done" % source.nick))
            except sqlao_e.NoResultFound:
                client.send(message.msg(target,
                    u"%s: you don't seem to have this track faved" % source.nick))
            except sqlao_e.NoResultFound:
                client.send(message.msg(target, u"%s: an error occured: %r" % (
                        source.nick, e)))    
        finally:
            session.close()
