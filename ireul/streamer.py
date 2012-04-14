from collections import deque
from ireul.environment import DBSession
from ireul.storage import models as m
from sqlalchemy.sql import func
from zope.interface import Interface, implements


class TrackSelectionStrategy(Interface):
    def get_tracks(num=1):
        """
        Return an iterable containing tracks to enqueued
        """
        pass


class RandomSelectionStrategy(object):
    implements(TrackSelectionStrategy)

    def __init__(self):
        self._sess = DBSession()

    def get_tracks(self, num=1):
        return self._sess.query(m.TrackOriginal).\
                order_by(func.random()).\
                limit(num).all()


class TrackQueue(object):
    def __init__(self, initial=[]):
        self._q = deque()

    def __len__(self):
        return len(self._q)

    def __repr__(self):
        return "TrackQueue(%r)" % self._q

    def enqueue(self, track):
        self._q.append(track)

    def pop(self):
        return self._q.popleft()

    def __iter__(self):
        return iter(list(self._q))


tq = TrackQueue()

def track_getter(src, min_queue, strat):
    while True:
        if len(src) < min_queue:
            for track in strat.get_tracks(min_queue - len(src)):
                src.enqueue(track)
        track_orig = src.pop()
        candidates = track_orig.derivatives.filter_by(codec='VorbisAudio')
        if candidates.count() == 0:
            # transcode
            pass
        elif candidates.count() == 1:
            yield candidates.one()
        else:
            print "too many candidates"
