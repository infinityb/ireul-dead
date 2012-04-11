import audiotools
import magic
import gevent.queue

from hanyuu2.storage.filesystem import cont_addr
from hanyuu2.storage.models import (
    TrackOriginal,
    TrackDerived,
    Blob,
)

import audiotools
import json

_magic = magic.Magic(mime=True)


def _ca_copy_contents(src_fh):
    dst_fh = cont_addr.open(mode='w')
    while True:
        buf = src_fh.read(4096)
        if not buf: break
        dst_fh.write(buf)
    src_fh.close()
    return dst_fh.close()

def insert_track(source_filename):
    mimetype = _magic.from_file(source_filename)
    hash_ = _ca_copy_contents(open(source_filename, 'rb'))
    source_file = audiotools.open(source_filename)
    metadata = source_file.get_metadata()
    return TrackOriginal(Blob(hash_, mimetype),
                         metadata,
                         metadata.artist_name,
                         metadata.track_name)

def transcode(track_original, target_codec, compression_params):
    """Return a track with a new codec and compression parameters"""
    if target_codec is not audiotools.VorbisAudio: # FIXME: remove
        raise TypeError, "Target codec must be audiotools.VorbisAudio for now"
    transcoded_ctr = track_original.derivatives.filter_by(
        _codec=target_codec.__name__,
        _compression_params=json.dumps(compression_params)).count()
    if transcoded_ctr > 0:
        raise Exception, "File already transcoded to this format."
    if not isinstance(track_original, TrackOriginal):
        raise TypeError, "first argument must be TrackOriginal, not %r" % \
                type(track_original)
    if not hasattr(target_codec, 'from_pcm'):
        raise TypeError, "first argument must have from_pcm method"
    target_codec.from_pcm("/tmp/cocks", track_original.open_audiotools().to_pcm())
    hash_ = _ca_copy_contents(open("/tmp/cocks", 'rb'))
    # FIXME: hardcoded mime
    blob = Blob(hash_, "audio/ogg")
    return TrackDerived(track_original, blob, target_codec.__name__,
                        compression_params)

