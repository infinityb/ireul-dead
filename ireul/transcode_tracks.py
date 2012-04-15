import sys
import struct
import audiotools
from ireul.environment import DBSession, create_all
from ireul.settings import ENCODE_PARAMS
from ireul.storage import models as m
from ireul.storage.filesystem import cont_addr
from ireul import utils as u
create_all()

session = DBSession()

for track in session.query(m.TrackOriginal).filter(
    m.TrackOriginal._id.in_(list(xrange(6519, 6532)))).all():
    encoding_params = audiotools.EncodingParams(**ENCODE_PARAMS)
    encoding_params['serial'], = struct.unpack('!I',
            track.blob.cont_addr[-8:].decode('hex'))
    track_deriv = track.derivatives.\
        filter_by(
            codec='VorbisAudio',
            encoding_params=encoding_params
        ).count()
    if track_deriv > 0:
        continue
    new_track = u.transcode(track, audiotools.VorbisAudio, encoding_params)
    session.add(new_track)
    session.commit()
