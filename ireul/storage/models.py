from datetime import datetime
from sqlalchemy.ext.hybrid import hybrid_property
import datetime, json, pickle
import audiotools
from .filesystem import cont_addr

class _unspecified(object):
    def __repr__(self):
        return "unspecified"

unspecified = _unspecified()


class Blob(object):
    def __init__(self, cont_addr, mime_type, added_at=unspecified):
        """
        added_at is now if unspecified
        """
        self._cont_addr = cont_addr
        self._mime_type = mime_type
        if added_at is unspecified:
            added_at = datetime.datetime.now()
        self._added_at = added_at

    @hybrid_property
    def cont_addr(self):
        return self._cont_addr

    def __repr__(self):
        return "%s.%s(%r, %r, %r)" % (
            type(self).__module__,
            type(self).__name__,
            self._cont_addr,
            self._mime_type,
            self._added_at)


class TrackOriginal(object):
    def __init__(self, blob, metadata=None, artist=None, title=None):
        self._blob = blob
        self.metadata = metadata
        self._artist = artist
        self._title = title

    def __repr__(self):
        return "%s.%s(%r, %r, %r, %r)" % (
            type(self).__module__,
            type(self).__name__,
            self._blob,
            self._metadata,
            self._artist,
            self._title)

    @hybrid_property
    def id(self):
        return self._id

    @hybrid_property
    def blob(self):
        return self._blob

    @property
    def metadata(self):
        return pickle.loads(self._metadata)

    @metadata.setter
    def metadata(self, val):
        self._metadata = pickle.dumps(val)

    @hybrid_property
    def artist(self):
        return self._artist

    @hybrid_property
    def title(self):
        return self._title

    def open(self):
        return cont_addr.open(self.blob.cont_addr)

    def open_audiotools(self):
        return audiotools.open(cont_addr.addr_to_path(self.blob.cont_addr))

    def get_name(self):
        if hasattr(self.metadata, 'album'):
            return u"%s [%s] - %s" % (
                self.artist, self.metadata.album, self.title)
        return u"%s - %s" % (self.artist, self.title)


class TrackDerived(object):
    def __init__(self, original, blob, codec,
                 encoding_params, added_at=unspecified):
        self.original = original
        self._blob = blob
        self._codec = codec
        self._encoding_params = encoding_params
        if added_at is unspecified:
            added_at = datetime.datetime.now()
        self._added_at = added_at

    def __repr__(self):
        return "%s.%s(%r, %r, %r, %r, %r)" % (
            type(self).__module__,
            type(self).__name__,
            self.original,
            self._blob,
            self._codec,
            self._encoding_params,
            self._added_at)

    @hybrid_property
    def id(self):
        return self._id

    @hybrid_property
    def blob(self):
        return self._blob

    @hybrid_property
    def codec(self):
        return self._codec

    @hybrid_property
    def encoding_params(self):
        return self._encoding_params

    def open(self):
        return cont_addr.open(self.blob.cont_addr)

    def open_audiotools(self):
        return audiotools.open(cont_addr.addr_to_path(self.blob.cont_addr))

    def get_metadata(self):
        return {
                'title': self.original.title,
                'artist': self.original.artist,
                }


class User(object):
    def __init__(self, username):
        self._username = username

    @hybrid_property
    def username(self):
        return self._username


class Fave(object):
    def __init__(self, user=None, track=None):
        self.user = user
        self.track = track


class TrackPlay(object):
    def __init__(self, track, played_at=unspecified):
        self.track = track
        if played_at is unspecified:
            played_at = datetime.datetime.now()
        self._played_at = played_at

    @hybrid_property
    def played_at(self):
        return self._played_at


from . import tables

from sqlalchemy.orm import mapper, relationship

mapper(Blob, tables.blob,
       column_prefix="_",
       properties={})

mapper(TrackOriginal, tables.track_orig,
       column_prefix="_",
       properties={
           '_blob': relationship(Blob),
           'derivatives': relationship(TrackDerived, lazy='dynamic'),
           'faves': relationship(Fave, lazy='dynamic'),
           'plays': relationship(TrackPlay, lazy='dynamic'),
       })

mapper(TrackDerived, tables.track_derived,
       column_prefix="_",
       properties={
           '_blob': relationship(Blob),
           'original': relationship(TrackOriginal),
       })

mapper(User, tables.user, column_prefix="_")

mapper(Fave, tables.fave,
       column_prefix="_",
       properties={
           'user': relationship(User),
           'track': relationship(TrackOriginal)
       })

mapper(TrackPlay, tables.track_play,
       column_prefix="_",
       properties={
           'track': relationship(TrackOriginal)
       })
