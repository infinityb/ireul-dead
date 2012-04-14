import zipfile

import sys
import audiotools
from ireul.environment import DBSession, create_all
from ireul.storage import models as m
from ireul.storage.filesystem import cont_addr
from ireul import utils as u
create_all()


zip_ = zipfile.ZipFile(sys.argv[1], 'r')

for info in zip_.infolist():
    tr_fh = zip_.open(info.filename, 'r')
    track = u.insert_track(tr_fh)
    tr_fh.close()

    metadata = track.metadata
    while len(metadata.images()) > 0:
        metadata.delete_image(metadata.images()[0])
    track.metadata = metadata

    session.add(track)
