import sys
import audiotools
from ireul.environment import DBSession, create_all
from ireul.storage import models as m
from ireul.storage.filesystem import cont_addr
from ireul import utils as u
create_all()


fn = sys.argv[1]
track = u.insert_track(fn)

session = DBSession()


if session.query(m.Blob).filter(m.Blob.cont_addr == \
        track.blob.cont_addr).count() == 0:
    metadata = track.metadata
    while len(metadata.images()) > 0:
        metadata.delete_image(metadata.images()[0])
    track.metadata = metadata
    session.add(track)

session.commit()
