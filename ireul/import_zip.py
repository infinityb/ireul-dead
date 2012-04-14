import zipfile

import sys
import audiotools
from ireul.environment import DBSession, create_all
from ireul.storage import models as m
from ireul.storage.filesystem import cont_addr
from ireul import utils as u
create_all()

class FakeSeekZipExtFile(object):
    def __init__(self, factory):
        self._factory = factory
        self._real = self._factory()

    def read(self, *a, **kw):
        return self._real.read(*a, **kw)

    def seek(self, loc):
        assert loc == 0
        self._real.close()
        self._real = self._factory()

    def close(self):
        return self._real.close()

zip_ = zipfile.ZipFile(sys.argv[1], 'r')
session = DBSession()
for info in zip_.infolist():
    print "opening: %r" % info.filename
    try:
        try:
            tr_fh = FakeSeekZipExtFile(lambda: zip_.open(info.filename, 'r'))
            track = u.insert_track(tr_fh)
        finally:
            tr_fh.close()

        metadata = track.metadata
        while len(metadata.images()) > 0:
            metadata.delete_image(metadata.images()[0])
        track.metadata = metadata

        if session.query(m.Blob).filter(
                m.Blob.cont_addr == track.blob.cont_addr).count() > 0:
            continue

        session.add(track)
        session.commit()
    except audiotools.UnsupportedFile:
        pass

